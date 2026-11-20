export default function HomePage() {
  return (
    <main className="hero">
      <p className="brand">Nudge</p>
      <h1>Your accounts, already thinking.</h1>
      <p className="lede">
        A personal CS agent for one book of business — risk, memory, and approved
        actions without the company-wide dashboard feel.
      </p>
      <div className="cta">
        <a href="/briefing">Open briefing</a>
        <a className="ghost" href="/chat">
          Chat with Nudge
        </a>
      </div>
    </main>
  );
}
