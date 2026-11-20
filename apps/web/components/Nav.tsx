import Link from "next/link";

const links = [
  { href: "/briefing", label: "Briefing" },
  { href: "/chat", label: "Chat" },
  { href: "/approvals", label: "Approvals" },
];

export function Nav() {
  return (
    <header className="topnav">
      <Link href="/" className="topnav-brand">
        Nudge
      </Link>
      <nav>
        {links.map((l) => (
          <Link key={l.href} href={l.href}>
            {l.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
