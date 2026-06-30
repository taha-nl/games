import { useEffect, useRef } from 'react'

export function Starfield() {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = ref.current
    if (!container) return
    for (let i = 0; i < 150; i++) {
      const star = document.createElement('div')
      star.className = 'star'
      const size = Math.random() * 2.5 + 0.5
      star.style.cssText = `
        width:${size}px; height:${size}px;
        top:${Math.random() * 100}%;
        left:${Math.random() * 100}%;
        --duration:${Math.random() * 4 + 1.5}s;
        --delay:${Math.random() * 4}s;
      `
      container.appendChild(star)
    }
    return () => { container.innerHTML = '' }
  }, [])

  return <div ref={ref} className="stars" aria-hidden />
}
