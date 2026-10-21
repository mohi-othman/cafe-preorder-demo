/** A generated two-note chime (WebAudio, no audio file). Browsers only allow sound after a tap: call unlockAudio() from one. */
let ctx: AudioContext | null = null;

export function unlockAudio() {
  ctx ??= new AudioContext();
  void ctx.resume();
}

export function playChime() {
  if (!ctx) return;
  const start = ctx.currentTime;
  [880, 1318.5].forEach((freq, i) => {
    const t = start + i * 0.18;
    const osc = ctx!.createOscillator();
    const gain = ctx!.createGain();
    osc.type = "sine";
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.0001, t);
    gain.gain.exponentialRampToValueAtTime(0.4, t + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.6);
    osc.connect(gain).connect(ctx!.destination);
    osc.start(t);
    osc.stop(t + 0.65);
  });
}
