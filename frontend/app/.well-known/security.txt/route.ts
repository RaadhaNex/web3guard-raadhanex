function siteUrl() {
  return (process.env.NEXT_PUBLIC_SITE_URL || process.env.NEXT_PUBLIC_FRONTEND_URL || "https://web3guard-raadhanex.vercel.app").replace(/\/$/, "");
}

export function GET() {
  const base = siteUrl();
  const body = [
    `Contact: ${base}/security`,
    `Policy: ${base}/responsible-use`,
    `Preferred-Languages: en, hi`,
    `Canonical: ${base}/.well-known/security.txt`,
    "Hiring: https://github.com/RaadhaNex/web3guard-raadhanex",
    "Acknowledgments: Security reports are reviewed manually. Do not test without authorization.",
    "",
  ].join("\n");

  return new Response(body, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
}
