import { useEffect, useLayoutEffect } from 'react'
import { useLocation, useNavigationType } from 'react-router-dom'

const savedPositions = new Map()

function ScrollManager() {
  const { key, hash } = useLocation()
  const navigationType = useNavigationType()

  useEffect(() => {
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual'
    }
  }, [])

  useLayoutEffect(() => {
    if (!hash) {
      const top = navigationType === 'POP' ? (savedPositions.get(key) ?? 0) : 0
      window.scrollTo({ top, behavior: 'instant' })
    }

    const remember = () => savedPositions.set(key, window.scrollY)
    window.addEventListener('scroll', remember, { passive: true })
    return () => window.removeEventListener('scroll', remember)
  }, [key, hash, navigationType])

  return null
}

export default ScrollManager
