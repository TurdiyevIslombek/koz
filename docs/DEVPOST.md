# Devpost texts (copy into the form)

**Name:** Ko'z

**Tagline:** Tell a camera what job to do — in Uzbek, Russian or English. It builds the job from tested OpenCV 5 blocks, tests itself, fixes itself, and stops in private places.

## Inspiration
Shops, schools and homes in Uzbekistan have cheap cameras, but setting up computer vision needs a programmer. And most camera AI is built for surveillance. I wanted a camera you can simply talk to, that refuses to spy.

## What it does
You type a job ("Do'konga kirgan odamlarni sana", "find the green ball", "найди мой телефон"). Ko'z turns it into a recipe of tested OpenCV 5 blocks, runs it on the live camera for 3 seconds, checks the result with OpenCV numbers, and if the check fails it changes one setting from what the camera measured (for example the ball's colour, hue 52 → 31) and tries again, up to 3 times. Then it runs: counting people through a doorway, following a round coloured thing, or finding 11 everyday objects.
Privacy is built into the code, not left to the AI: faces are blurred before anything else, frames never leave the computer, and a privacy guard stops the camera when it sees a toilet, a bed, a sink in a bathroom, or a covered lens. It refuses identity, profiling, hidden cameras and audio.

## How I built it
Python + OpenCV 5 (YuNet faces, NanoDet objects, Places365 rooms, colour and line-crossing blocks), a fixed recipe contract checked by code, a WebSocket runner on the Mac, and a web app on AWS (CloudFormation, EC2, DynamoDB with auto-delete) that receives only numbers. Built with Claude and Codex as coding assistants (logged in AI_LOG.md); the product's own agent loop is separate.

## Results (measured, failures kept)
Live camera: every private view tried was stopped (toilet, bathroom sink, bed, covered lens); one possible false stop. The agent fixed a wrong colour on the live camera (52 → 31) and then followed the ball. Counter: 11 in / 9 out in one session — at least one miscount. Planner: 20/20 on fresh sentences after tuning (honestly marked as tuned); Gemma 14/20 on the laptop. Full details: docs/TRIALS.md.

## Challenges
A room classifier called my bedroom an "airplane cabin", so the guard now stops on objects it can see. The fly-brain robot car is built and passes software tests, but real trials were stopped for safety when the camera board overheated.

## What's next
Find anything from words (open-vocabulary detection), several cameras in one job, a privacy-first exam-integrity mode, and running my own Uzbek model as the planner.

**Links:** https://github.com/TurdiyevIslombek/koz · https://16.178.45.27/
