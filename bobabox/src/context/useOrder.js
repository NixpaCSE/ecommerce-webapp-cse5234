import { useContext } from 'react'
import { OrderContext } from './OrderContext.js'

export function useOrder() {
  const context = useContext(OrderContext)
  if (!context) throw new Error('useOrder must be used inside <OrderProvider>')
  return context
}
