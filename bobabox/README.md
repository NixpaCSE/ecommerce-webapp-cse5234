# BobaBox (front end)

React + Vite + React Router v6.

## Run it

```bash
cd bobabox
npm install
npm run dev
```

Open http://localhost:5173 (it redirects to `/purchase`).

## Pages

| URL | File | Status |
| --- | --- | --- |
| `/purchase` | `src/components/Purchase.jsx` | Done |
| `/purchase/paymentEntry` | `src/components/PaymentEntry.jsx` | Stub |
| `/purchase/shippingEntry` | `src/components/ShippingEntry.jsx` | Stub |
| `/purchase/viewOrder` | `src/components/ViewOrder.jsx` | Stub |
| `/purchase/viewConfirmation` | `src/components/Confirmation.jsx` | Stub |

Routes are defined in `src/App.jsx`. Each stub has a TODO comment describing what it needs.

## Shared order state

Cart, payment, and shipping data live in React Context (`src/context/OrderProvider.jsx`),
so they persist across all pages. Read or update them from any component:

```jsx
import { useOrder } from '../context/useOrder.js'

const {
  cart,            // [{ id, name, price, quantity }]
  cartCount,       // total number of kits
  cartTotal,       // total price
  addToCart,       // (product, quantity)
  updateQuantity,  // (id, quantity) — 0 removes the line
  removeFromCart,  // (id)
  payment,         // { creditCardNumber, expirationDate, cvvCode, cardHolderName }
  setPayment,
  shipping,        // { name, addressLine1, addressLine2, city, state, zip }
  setShipping,
  resetOrder,      // clears everything after the order is placed
} = useOrder()
```

The cart is also saved to `localStorage`, so it survives a page refresh.

## Other files

- `src/data/products.js` – hardcoded catalog of 5 boba kits (moves to the backend in Labs 7–8)
- `src/components/Header.jsx` / `Cart.jsx` – top bar and slide-out cart (available on every page)
- `src/utils/format.js` – `formatPrice()` helper
