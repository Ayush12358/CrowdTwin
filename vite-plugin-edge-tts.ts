// Use the global WebSocket provided by Bun to avoid the node:http 101 upgrade bug
import { v4 as uuidv4 } from 'uuid'
import crypto from 'crypto'
import type { Plugin } from 'vite'

const TRUSTED_TOKEN = '6A5AA1D4EAFF4E9FB37E23D68491D6F4'
const CHROMIUM_VERSION = '143.0.3650.75'
const SEC_MS_GEC_VERSION = `1-${CHROMIUM_VERSION}`

const VOICES: Record<string, string> = {
    ayush: 'en-GB-RyanNeural',
    jayanth: 'en-US-BrianMultilingualNeural',
    prabhav: 'en-US-GuyNeural',
    default: 'en-US-GuyNeural',
}

async function synthesize(text: string, voiceKey: string): Promise<Buffer> {
    let serverTime = Date.now()
    try {
        const timeRes = await fetch(
            `https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/voices/list?trustedclienttoken=${TRUSTED_TOKEN}`,
            { method: 'HEAD' }
        )
        const dateHeader = timeRes.headers.get('date')
        if (dateHeader) {
            serverTime = new Date(dateHeader).getTime()
        }
    } catch (e) {
        // Fallback
    }

    const WIN_EPOCH = 11644473600n
    let ticks = BigInt(Math.floor(serverTime / 1000)) + WIN_EPOCH
    ticks -= ticks % 300n
    ticks *= 10000000n
    const strToHash = ticks.toString() + TRUSTED_TOKEN
    const secMsGec = crypto.createHash('sha256').update(strToHash, 'ascii').digest('hex').toUpperCase()

    const connectionId = uuidv4().replace(/-/g, "").toUpperCase()
    const url = `wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=${TRUSTED_TOKEN}&ConnectionId=${connectionId}&Sec-MS-GEC=${secMsGec}&Sec-MS-GEC-Version=${SEC_MS_GEC_VERSION}`

    return new Promise((resolve, reject) => {
        // Bun native WebSocket supports headers in the second argument
        const ws = new WebSocket(url, {
            headers: {
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
                'User-Agent': `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/${CHROMIUM_VERSION.split('.')[0]}.0.0.0 Safari/537.36 Edg/${CHROMIUM_VERSION.split('.')[0]}.0.0.0`,
                'Origin': 'chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold',
                'Sec-MS-GEC': secMsGec,
                'Sec-MS-GEC-Version': SEC_MS_GEC_VERSION
            }
        } as any) // Cast to any because TS DOM types don't know about Bun's headers extension

        ws.binaryType = 'arraybuffer'

        const audioChunks: Buffer[] = []
        let timedOut = false
        const timeout = setTimeout(() => {
            timedOut = true
            ws.close()
            reject(new Error('Edge TTS timeout'))
        }, 15000)

        ws.addEventListener('open', () => {
            const configMsg =
                `X-Timestamp:${new Date(serverTime).toISOString()}\r\n` +
                `Content-Type:application/json; charset=utf-8\r\n` +
                `Path:speech.config\r\n\r\n` +
                `{"context":{"synthesis":{"audio":{"metadataoptions":{"sentenceBoundaryEnabled":"false","wordBoundaryEnabled":"true"},"outputFormat":"audio-24khz-48kbitrate-mono-mp3"}}}}`

            ws.send(configMsg)

            const escapedText = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
            const locale = voiceKey.split('-').slice(0, 2).join('-')
            const shortName = voiceKey.split('-').pop()
            const fullVoiceName = `Microsoft Server Speech Text to Speech Voice (${locale}, ${shortName})`

            const ssmlText = `<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='en-US'>` +
                `<voice name='${fullVoiceName}'>` +
                `<prosody pitch='+0Hz' rate='+10%'>${escapedText}</prosody>` +
                `</voice></speak>`

            const ssmlMsg =
                `X-RequestId:${connectionId}\r\n` +
                `Content-Type:application/ssml+xml\r\n` +
                `X-Timestamp:${new Date(serverTime).toISOString()}Z\r\n` +
                `Path:ssml\r\n\r\n` +
                ssmlText

            ws.send(ssmlMsg)
        })

        ws.addEventListener('message', (event) => {
            const data = (event as MessageEvent).data
            if (data instanceof ArrayBuffer) {
                const buffer = Buffer.from(data)
                // The first 2 bytes dictate the length of the metadata header.
                const headerLength = buffer.readUInt16BE(0)
                const audioData = buffer.subarray(headerLength + 2)
                if (audioData.length > 0) {
                    audioChunks.push(audioData)
                }
            } else if (typeof data === 'string') {
                if (data.includes('Path:turn.end')) {
                    clearTimeout(timeout)
                    ws.close()
                    resolve(Buffer.concat(audioChunks))
                } else if (data.includes('Path:response') && data.includes('403')) {
                    clearTimeout(timeout)
                    ws.close()
                    reject(new Error('Edge TTS 403 Forbidden'))
                }
            }
        })

        ws.addEventListener('error', (e) => {
            if (!timedOut) {
                clearTimeout(timeout)
                reject(new Error('WebSocket Error: ' + (e as ErrorEvent).message))
            }
        })

        ws.addEventListener('close', () => {
            if (!timedOut && audioChunks.length > 0) {
                clearTimeout(timeout)
                resolve(Buffer.concat(audioChunks))
            } else if (!timedOut) {
                clearTimeout(timeout)
                reject(new Error('WebSocket closed without audio data'))
            }
        })
    })
}

export default function edgeTtsPlugin(): Plugin {
    return {
        name: 'edge-tts-proxy',
        configureServer(server) {
            server.middlewares.use(async (req, res, next) => {
                if (!req.url?.startsWith('/api/edge-tts')) return next()

                const url = new URL(req.url, 'http://localhost')
                const text = url.searchParams.get('text')
                const voiceKey = url.searchParams.get('voice') || 'default'

                if (!text) {
                    res.writeHead(400, { 'Content-Type': 'application/json' })
                    res.end(JSON.stringify({ error: 'Missing text parameter' }))
                    return
                }

                const voice = VOICES[voiceKey] || VOICES.default

                try {
                    const audioBuffer = await synthesize(text, voice)
                    res.writeHead(200, {
                        'Content-Type': 'audio/mpeg',
                        'Content-Length': audioBuffer.length,
                        'Cache-Control': 'no-cache',
                    })
                    res.end(audioBuffer)
                } catch (error: any) {
                    console.error('[edge-tts] Error:', error.message)
                    res.writeHead(500, { 'Content-Type': 'application/json' })
                    res.end(JSON.stringify({ error: 'TTS synthesis failed', details: error.message }))
                }
            })
        }
    }
}
