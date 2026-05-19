import Image from "next/image";
import styles from "./KavachWingNavLogo.module.css";

type KavachWingNavLogoProps = { showText?: boolean };

export default function KavachWingNavLogo({ showText = false }: KavachWingNavLogoProps) {
  return (
    <div className={styles.wrap} aria-label="Web3Guard AI brand mark">
      <div className={styles.icon}>
        <Image src="/brand/kavachwing-emblem.webp" alt="Web3Guard AI emblem" width={96} height={96} priority />
      </div>
      {showText ? (
        <div className={styles.text}>
          <strong>Web3Guard AI</strong>
          <span>by RAADHANEX</span>
        </div>
      ) : null}
    </div>
  );
}
