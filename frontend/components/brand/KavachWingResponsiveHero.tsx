"use client";

import Image from "next/image";
import styles from "./KavachWingResponsiveHero.module.css";

type KavachWingResponsiveHeroProps = {
  priority?: boolean;
  variant?: "hero" | "compact" | "splash";
};

export default function KavachWingResponsiveHero({
  priority = true,
  variant = "hero",
}: KavachWingResponsiveHeroProps) {
  return (
    <section
      className={`${styles.wrap} ${styles[variant]}`}
      aria-label="KavachWing brand hero"
    >
      <div className={styles.glowOne} />
      <div className={styles.glowTwo} />

      <picture className={styles.picture}>
        <source
          media="(max-width: 640px)"
          srcSet="/brand/kavachwing-splash.webp"
        />
        <source
          media="(max-width: 1024px)"
          srcSet="/brand/kavachwing-emblem.webp"
        />
        <img
          className={styles.image}
          src="/brand/kavachwing-hero.webp"
          alt="KavachWing Web3 Launch-Readiness Scanner"
        />
      </picture>

      <div className={styles.floatEmblem} aria-hidden="true">
        <Image
          src="/brand/kavachwing-emblem.png"
          alt=""
          width={420}
          height={420}
          priority={priority}
        />
      </div>
    </section>
  );
}
