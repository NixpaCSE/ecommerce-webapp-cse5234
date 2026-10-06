# BobaBox (front end)

React + Vite + React Router v6.

## Getting started

```bash
git clone https://github.com/NixpaCSE/ecommerce-webapp-cse5234.git
cd ecommerce-webapp-cse5234/bobabox
npm install
npm run dev
```

Open http://localhost:5173 (it redirects to `/purchase`).

## Team workflow

Don't push straight to `main`. Work on your own branch and open a PR:

```bash
git checkout main && git pull          # start from the latest main
git checkout -b feature/payment-entry  # one branch per page/feature
# ...make changes...
git add . && git commit -m "add payment entry form"
git push -u origin feature/payment-entry
```

Then open a pull request on GitHub and have someone look it over before merging.
Try to only edit your own page file so we don't get merge conflicts.

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

## Styling

Keep pages consistent with the purchase page (white background, black text, light gray cards):

- **Colors** – use the variables in `src/index.css` (`--ink`, `--muted`, `--surface`, `--border`) instead of new hex codes.
- **Buttons** – `className="primary-button"` (black pill button).
- **Inputs** – match the rounded `qty-input` style (1.5px `--border` outline, black on focus).
- **Headings** – lowercase, heavy, tight: see `.hero-title` in `src/App.css`.
- **Sections/cards** – `--surface` background with a large border radius (like `.product-card`).
- **Prices** – always use `formatPrice()` from `src/utils/format.js`.
- **Item images** – `<Swatch gradient={...} size="small" />` shows a kit's color (see `Cart.jsx`).

Put new styles in `src/App.css` under a comment for your page.

## Other files

- `src/data/products.js` – hardcoded catalog of 5 boba kits (moves to the backend in Labs 7–8)
- `src/components/Header.jsx` / `Cart.jsx` – top bar and slide-out cart (available on every page)
- `src/components/Swatch.jsx` – gradient circle shown for each kit
- `src/components/ProductPreview.jsx` – popup with the product photo (click a kit's circle)
- `public/images/` – product photos (photos from [Takes Two Eggs](https://takestwoeggs.com))
- `src/utils/format.js` – `formatPrice()` helper
