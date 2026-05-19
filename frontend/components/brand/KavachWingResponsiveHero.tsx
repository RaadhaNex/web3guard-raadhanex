"use client";

import Image from "next/image";
import styles from "./KavachWingResponsiveHero.module.css";

type KavachWingResponsiveHeroProps = {
  priority?: boolean;
  variant?: "hero" | "compact" | "splash";
};

export default function KavachWingResponsiveHero({
  priority = false,
  variant = "compact",
}: KavachWingResponsiveHeroProps) {
  return (
    <section
      className={`${styles.wrap} ${styles[variant]}`}
      aria-label="Web3Guard AI brand animation"
    >
      <div className={styles.glowOne} />
      <div className={styles.glowTwo} />

      <picture className={styles.picture}>
        <source media="(max-width: 640px)" srcSet="/brand/kavachwing-splash.webp" />
        <source media="(max-width: 1024px)" srcSet="/brand/kavachwing-emblem.webp" />
        <img className={styles.image} src="/brand/kavachwing-hero.webp" alt="Web3Guard AI animated brand visual" />
      </picture>

      <div className={styles.floatEmblem} aria-hidden="true">
        <Image src="/brand/kavachwing-emblem.webp" alt="" width={420} height={420} priority={priority} />
      </div>
    </section>
  );
}
