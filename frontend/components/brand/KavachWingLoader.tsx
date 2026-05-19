"use client";

import Image from "next/image";
import styles from "./KavachWingLoader.module.css";

type KavachWingLoaderProps = {
  fullScreen?: boolean;
  showText?: boolean;
};

export default function KavachWingLoader({
  fullScreen = true,
  showText = true,
}: KavachWingLoaderProps) {
  return (
    <div className={fullScreen ? styles.screen : styles.box} aria-label="KavachWing loading">
      <div className={styles.orbit}>
        <span className={`${styles.ring} ${styles.ringOne}`} />
        <span className={`${styles.ring} ${styles.ringTwo}`} />
        <span className={`${styles.ring} ${styles.ringThree}`} />

        <div className={styles.logo3d}>
          <Image src="/brand/kavachwing-emblem.png" alt="KavachWing" width={520} height={520} priority />
        </div>

        <span className={`${styles.particle} ${styles.particleOne}`} />
        <span className={`${styles.particle} ${styles.particleTwo}`} />
        <span className={`${styles.particle} ${styles.particleThree}`} />
        <span className={`${styles.particle} ${styles.particleFour}`} />
      </div>

      {showText ? (
        <div className={styles.textBlock}>
          <h1>KavachWing</h1>
          <p>by RAADHANEX</p>
          <small>Scan. Fix. Launch safer.</small>
        </div>
      ) : null}
    </div>
  );
}
