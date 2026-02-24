import { WebSocket } from 'ws'
import { randomUUID } from 'crypto'
import type { Plugin } from 'vite'

const WSS_URL = 'wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1'
const TRUSTED_TOKEN = '6A5AA1D4EAFF4E9FB37E23D68491D6F4'

const VOICES: Record<string, string> = {
    ayush: 'en-GB-RyanNeural',
    jayanth: 'en-US-BrianMultilingualNeural',
    prabhav: 'en-US-GuyNeural',
    default: 'en-US-GuyNeural',
}

function buildSSML(text: string, voice: string): string {
    const escaped = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
    return `<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>` +
        `<voice name='${voice}'>` +
        `<prosody pitch='+0Hz' rate='+10%' volume='+0%'>${escaped}</prosody>` +
        `</voice></speak>`
}

function synthesize(text: string, voice: string): Promise<Buffer> {
    return new Promise((resolve, reject) => {
        const requestId = randomUUID().replace(/-/g, '')
        const url = `${WSS_URL}?TrustedClientToken=${TRUSTED_TOKEN}&ConnectionId=${requestId}`

        const ws = new WebSocket(url, {
            headers: {
                'Origin': 'chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
            }
        })

        const audioChunks: Buffer[] = []
        let timedOut = false
        const timeout = setTimeout(() => {
            timedOut = true
            ws.close()
            reject(new Error('Edge TTS timeout'))
        }, 30000)

        ws.on('open', () => {
            // Send config
            ws.send(
                `Content-Type:application/json; charset=utf-8\r\n` +
                `Path:speech.config\r\n\r\n` +
                `{"context":{"synthesis":{"audio":{"metadataoptions":{"sentenceBoundaryEnabled":"false","wordBoundaryEnabled":"false"},"outputFormat":"audio-24khz-96kbitrate-mono-mp3"}}}}`
            )

            // Send SSML
            const ssml = buildSSML(text, voice)
            ws.send(
                `X-RequestId:${requestId}\r\n` +
                `Content-Type:application/ssml+xml\r\n` +
                `Path:ssml\r\n\r\n` +
                ssml
            )
        })

        ws.on('message', (data: Buffer | string, isBinary: boolean) => {
            if (isBinary && Buffer.isBuffer(data)) {
                // Binary frame: header (2-byte length + header string) + audio data
                const headerLen = data.readUInt16BE(0)
                const audioData = data.subarray(2 + headerLen)
                if (audioData.length > 0) {
                    audioChunks.push(audioData)
                }
            } else {
                const msg = data.toString()
                if (msg.includes('Path:turn.end')) {
                    clearTimeout(timeout)
                    ws.close()
                    resolve(Buffer.concat(audioChunks))
                }
            }
        })

        ws.on('error', (err) => {
            if (!timedOut) {
                clearTimeout(timeout)
                reject(err)
            }
        })

        ws.on('close', () => {
            if (!timedOut && audioChunks.length > 0) {
                clearTimeout(timeout)
                resolve(Buffer.concat(audioChunks))
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
                    console.log(`[edge-tts] Synthesizing (${voice}): "${text.substring(0, 60)}..."`)
                    const audio = await synthesize(text, voice)

                    res.writeHead(200, {
                        'Content-Type': 'audio/mpeg',
                        'Content-Length': audio.length.toString(),
                        'Cache-Control': 'public, max-age=3600',
                    })
                    res.end(audio)
                } catch (err) {
                    console.error('[edge-tts] Error:', err)
                    res.writeHead(500, { 'Content-Type': 'application/json' })
                    res.end(JSON.stringify({ error: 'TTS synthesis failed' }))
                }
            })
        },
    }
}
