import Image from "next/image";
import styles from "./KavachWingNavLogo.module.css";

type KavachWingNavLogoProps = { showText?: boolean };

export default function KavachWingNavLogo({ showText = true }: KavachWingNavLogoProps) {
  return (
    <div className={styles.wrap}>
      <div className={styles.icon}>
        <Image src="/brand/kavachwing-emblem.png" alt="Web3Guard AI by RAADHANEX" width={96} height={96} priority />
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
