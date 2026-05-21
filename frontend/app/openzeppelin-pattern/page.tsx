import { OpenZeppelinPatternClient } from "@/components/openzeppelin-pattern/OpenZeppelinPatternClient";

export const metadata = {
  title: "OpenZeppelin Pattern Intelligence | Web3Guard AI",
  description: "Compare supplied Solidity evidence against common OpenZeppelin-style secure-contract patterns without claiming official certification or audit status.",
};

export default function OpenZeppelinPatternPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="clean-panel p-6 sm:p-8">
        <p className="section-label">OpenZeppelin Pattern Intelligence</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">
          Compare contracts against battle-tested secure pattern expectations.
        </h1>
        <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Web3Guard checks supplied Solidity/import evidence for common OpenZeppelin-style patterns such as ERC standards, Ownable/AccessControl, ReentrancyGuard, Pausable, SafeERC20, and upgradeability safety. It is not an official OpenZeppelin scanner and not a certified audit.
        </p>
      </section>

      <OpenZeppelinPatternClient />
    </main>
  );
}
