import { useEffect, useId, useState } from "react";

/**
 * HeroInkRibbon renders a confined layered SVG ribbon inside the landing hero.
 * It omits SMIL animation nodes entirely when reduced motion is preferred.
 */
export function HeroInkRibbon() {
  const [shouldAnimate, setShouldAnimate] = useState(false);
  const instanceId = useId().replace(/:/g, "");

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

    const syncMotionPreference = () => {
      setShouldAnimate(!mediaQuery.matches);
    };

    syncMotionPreference();

    if (typeof mediaQuery.addEventListener === "function") {
      mediaQuery.addEventListener("change", syncMotionPreference);
      return () => mediaQuery.removeEventListener("change", syncMotionPreference);
    }

    mediaQuery.addListener(syncMotionPreference);
    return () => mediaQuery.removeListener(syncMotionPreference);
  }, []);

  const backFilterId = `${instanceId}-flow-back`;
  const frontFilterId = `${instanceId}-flow-front`;
  const shineFilterId = `${instanceId}-flow-shine`;

  return (
    <div className="if-hero-ink-ribbon" aria-hidden="true">
      <svg
        className="if-hero-ink-ribbon-svg"
        viewBox="0 0 800 900"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <filter id={backFilterId} x="-30%" y="-30%" width="160%" height="160%">
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.011 0.005"
              numOctaves="3"
              seed="3"
              result="t"
            >
              {shouldAnimate ? (
                <animate
                  attributeName="baseFrequency"
                  values="0.011 0.005;0.017 0.008;0.011 0.005"
                  dur="40s"
                  repeatCount="indefinite"
                />
              ) : null}
            </feTurbulence>
            <feDisplacementMap in="SourceGraphic" in2="t" scale="110" />
          </filter>

          <filter id={frontFilterId} x="-30%" y="-30%" width="160%" height="160%">
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.016 0.007"
              numOctaves="3"
              seed="6"
              result="t"
            >
              {shouldAnimate ? (
                <animate
                  attributeName="baseFrequency"
                  values="0.016 0.007;0.024 0.011;0.016 0.007"
                  dur="30s"
                  repeatCount="indefinite"
                />
              ) : null}
            </feTurbulence>
            <feDisplacementMap in="SourceGraphic" in2="t" scale="75" />
          </filter>

          <filter id={shineFilterId} x="-30%" y="-30%" width="160%" height="160%">
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.02 0.009"
              numOctaves="2"
              seed="14"
              result="t"
            >
              {shouldAnimate ? (
                <animate
                  attributeName="baseFrequency"
                  values="0.02 0.009;0.03 0.014;0.02 0.009"
                  dur="22s"
                  repeatCount="indefinite"
                />
              ) : null}
            </feTurbulence>
            <feDisplacementMap in="SourceGraphic" in2="t" scale="50" />
          </filter>
        </defs>

        <polygon
          className="if-hero-ink-ribbon-back"
          points="60,-80 440,-80 740,980 340,980"
          fill="var(--color-accent)"
          filter={`url(#${backFilterId})`}
        >
          {shouldAnimate ? (
            <animateTransform
              attributeName="transform"
              type="translate"
              values="0 0; 18 -25; -12 18; 0 0"
              dur="40s"
              repeatCount="indefinite"
            />
          ) : null}
        </polygon>

        <polygon
          className="if-hero-ink-ribbon-front"
          points="160,-60 360,-60 600,960 420,960"
          fill="var(--color-accent)"
          filter={`url(#${frontFilterId})`}
        >
          {shouldAnimate ? (
            <animateTransform
              attributeName="transform"
              type="translate"
              values="0 0; -14 20; 10 -15; 0 0"
              dur="30s"
              repeatCount="indefinite"
            />
          ) : null}
        </polygon>

        <polygon
          className="if-hero-ink-ribbon-shine"
          points="280,-40 330,-40 480,940 430,940"
          fill="var(--color-accent)"
          filter={`url(#${shineFilterId})`}
        >
          {shouldAnimate ? (
            <animateTransform
              attributeName="transform"
              type="translate"
              values="0 0; 30 -10; -25 15; 0 0"
              dur="22s"
              repeatCount="indefinite"
            />
          ) : null}
        </polygon>
      </svg>
      <div className="if-hero-ink-ribbon-fade" />
    </div>
  );
}
