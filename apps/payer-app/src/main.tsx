import { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Lang = "en" | "hi" | "ta" | "te";
type Reason = { code: string; text: string; text_localized: string };
type Score = { tier: "allow" | "warn" | "hold"; reasons: Reason[]; hold_id?: string; guardian_link?: string; guardian_required: boolean; degraded: boolean };

const api = "http://localhost:8000";
const copy: Record<Lang, { greeting: string; pay: string; collect: string; title: string }> = {
  en: { greeting: "Good evening, Asha", pay: "Pay someone", collect: "Review request", title: "Pause and check" },
  hi: { greeting: "शुभ संध्या, आशा", pay: "भुगतान करें", collect: "अनुरोध देखें", title: "रुककर जांच करें" },
  ta: { greeting: "மாலை வணக்கம், ஆஷா", pay: "பணம் செலுத்து", collect: "கோரிக்கையைப் பார்", title: "நிறுத்திச் சரிபாருங்கள்" },
  te: { greeting: "శుభ సాయంత్రం, ఆశా", pay: "చెల్లించండి", collect: "అభ్యర్థనను చూడండి", title: "ఆగి తనిఖీ చేయండి" }
};

function App() {
  const [lang, setLang] = useState<Lang>("ta");
  const [channel, setChannel] = useState<"pay" | "collect">("collect");
  const [payee, setPayee] = useState("quickcash77@bankC");
  const [amount, setAmount] = useState("24500");
  const [score, setScore] = useState<Score | null>(null);
  const [message, setMessage] = useState("");
  const [guardianToken, setGuardianToken] = useState<string | null>(null);
  const labels = copy[lang];
  const holdLink = useMemo(() => score?.guardian_link ? `${window.location.origin}${score.guardian_link}` : "", [score]);

  useEffect(() => {
    const token = window.location.pathname.startsWith("/g/") ? window.location.pathname.slice(3) : null;
    if (token) { setGuardianToken(token); void guardianPage(token); }
  }, []);

  async function guardianPage(token: string) {
    const response = await fetch(`${api}/v1/guardian/${token}`);
    if (!response.ok) { setMessage("This guardian link is no longer valid."); return; }
    const data = await response.json();
    setMessage(`Guardian review: ₹${data.hold.amount_inr.toLocaleString("en-IN")} to ${data.hold.payee_vpa}. ${data.hold.reason}`);
  }

  async function guardianDecision(decision: "approve" | "reject") {
    if (!guardianToken) return;
    const preview = await fetch(`${api}/v1/guardian/${guardianToken}`);
    const data = await preview.json();
    const response = await fetch(`${api}/v1/holds/${data.hold.id}/decision`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ token: guardianToken, decision }) });
    setMessage(response.ok ? (decision === "approve" ? "Payment released for Asha." : "Payment cancelled. Thanks for checking.") : "This guardian link can no longer be used.");
  }

  async function assess() {
    setMessage("");
    const response = await fetch(`${api}/v1/risk/score`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ payer_vpa: "asha@bankA", payee_vpa: payee, amount_inr: Number(amount), channel, timestamp: new Date().toISOString(), lang }) });
    setScore(await response.json());
  }

  function speak() {
    const words = score?.reasons.map((reason) => reason.text_localized).join(" ") ?? "";
    speechSynthesis.speak(new SpeechSynthesisUtterance(words));
  }

  async function cancel() {
    if (score?.hold_id) await fetch(`${api}/v1/holds/${score.hold_id}/cancel`, { method: "POST" });
    setScore(null); setMessage("Payment cancelled. Thanks for checking.");
  }

  if (guardianToken) return <main className="app guardian" aria-live="polite"><header><div className="brand-mark">S</div><div><strong>SETU</strong><span>Guardian review</span></div></header><section className="sheet hold"><span className="tier">Approval requested</span><h2>Help Asha pause and check</h2><p>{message || "Loading payment details…"}</p><button className="primary" onClick={() => void guardianDecision("reject")}>Reject payment</button><button className="secondary" onClick={() => void guardianDecision("approve")}>Approve payment</button></section></main>;
  return <main className="app" aria-live="polite">
    <header><div className="brand-mark">S</div><div><strong>SETU</strong><span>Shield</span></div><select aria-label="Language" value={lang} onChange={(event) => setLang(event.target.value as Lang)}>{(["en", "hi", "ta", "te"] as Lang[]).map((value) => <option key={value} value={value}>{value.toUpperCase()}</option>)}</select></header>
    <section className="hero"><p>{labels.greeting}</p><h1>₹ 18,420.50</h1><small>Available balance</small></section>
    {!score && <section className="card form"><h2>{labels.pay}</h2><div className="switch"><button className={channel === "pay" ? "selected" : ""} onClick={() => setChannel("pay")}>{labels.pay}</button><button className={channel === "collect" ? "selected" : ""} onClick={() => setChannel("collect")}>{labels.collect}</button></div><label>UPI ID<input value={payee} onChange={(event) => setPayee(event.target.value)} /></label><label>Amount<input inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value)} /></label><button className="primary" onClick={() => void assess()}>Continue</button></section>}
    {score && <section className={`sheet ${score.tier}`}><span className="tier">{score.tier === "hold" ? "Payment on hold" : score.tier === "warn" ? "Check before paying" : "Looks normal"}</span><h2>{score.tier === "allow" ? "Ready to pay" : labels.title}</h2>{score.degraded && <p className="muted">Safety checks are temporarily unavailable. This payment was not blocked.</p>}<ul>{score.reasons.map((reason) => <li key={reason.code}>{reason.text_localized}</li>)}</ul>{score.reasons.length > 0 && <button className="voice" onClick={speak}>Play voice warning</button>}{score.tier === "hold" && <><p>Waiting for Arun, your trusted contact. The payment will cancel if nobody approves it.</p><button className="primary" onClick={() => navigator.clipboard.writeText(holdLink)}>Copy guardian link</button><button className="secondary" onClick={() => void cancel()}>Cancel payment</button></>}{score.tier === "warn" && <><button className="primary" onClick={() => setMessage("Payment sent through the mock rail.")}>Pay anyway</button><button className="secondary" onClick={() => setScore(null)}>Go back</button></>}{score.tier === "allow" && <button className="primary" onClick={() => setMessage("Payment sent through the mock rail.")}>Pay ₹{amount}</button>}</section>}
    {message && <p className="toast">{message}</p>}
    <section className="recent"><h2>Recent people</h2><p>Amma <span>₹500</span></p><p>Green Mart <span>₹320</span></p><p>Metro card <span>₹150</span></p></section>
  </main>;
}
createRoot(document.getElementById("root")!).render(<App />);
