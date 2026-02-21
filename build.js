import { build } from 'vite';

async function runBuild() {
    try {
        await build();
        console.log("Build successful!");
    } catch (e) {
        console.log("BUILD FAILED:");
        console.log(e ? e.message : "Undefined error");
        if (e) {
            console.log(e.stack);
            console.log(JSON.stringify(e, null, 2));
        }
    }
}

runBuild();
