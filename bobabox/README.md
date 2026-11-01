# BobaBox (front end)

The presentation tier: a React + Vite + React Router single-page app. See the [root README](../README.md) for the full three-tier architecture.

## Getting started

```bash
git clone https://github.com/NixpaCSE/ecommerce-webapp-cse5234.git
cd ecommerce-webapp-cse5234/bobabox
npm install
npm run dev
```

Open http://localhost:5173.

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

## Pages

| URL | File | Purpose |
| --- | --- | --- |
| `/` | `src/components/Home.jsx` | Landing page: hero, how it works, flavors |
| `/purchase` | `src/components/Purchase.jsx` | Product catalog with add-to-cart |
| `/purchase/paymentEntry` | `src/components/PaymentEntry.jsx` | Checkout step 1: payment |
| `/purchase/shippingEntry` | `src/components/ShippingEntry.jsx` | Checkout step 2: shipping and email |
| `/purchase/viewOrder` | `src/components/ViewOrder.jsx` | Checkout step 3: review and place the order |
| `/purchase/viewConfirmation` | `src/components/Confirmation.jsx` | Confirmation number and order summary |
| `/about` | `src/components/About.jsx` | Mission, vision, strategy, and team |
| `/contact` | `src/components/Contact.jsx` | Support, returns, and FAQ |

Routes are defined in `src/App.jsx`. Unknown URLs redirect to `/`.

## Talking to the business tier

All network calls live in `src/api/inventory.js`:

- `fetchInventory()` – `GET /inventory-management/inventory/`, used to load the catalog
- `submitOrder()` – `POST /order-processing/order`, used when the customer places an order

The default base URL is the deployed `test` stage. To point at another stage, set `VITE_API_BASE_URL` in a local `.env.local` file:

```env
VITE_API_BASE_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/test
```

Orders are sent as `text/plain` so the browser treats them as a simple CORS request; the Lambda still parses the JSON body. Only the last 4 card digits, the cardholder name, and the expiration date are sent. The CVV is never sent.

If the order service rejects an order for insufficient stock (`409`), the review page shows how many of that kit are available and keeps the cart so the customer can adjust it.

## Shared order state

Products, cart, payment, and shipping live in React Context (`src/context/OrderProvider.jsx`), so they persist across pages. Read or update them from any component:

```jsx
import { useOrder } from '../context/useOrder.js'

const {
  products,        // catalog from the inventory API
  productsLoading,
  productsError,
  cart,            // [{ id, name, price, quantity }]
  cartCount,       // total number of kits
  cartTotal,       // total price
  addToCart,       // (product, quantity)
  updateQuantity,  // (id, quantity) — 0 removes the line
  removeFromCart,  // (id)
  payment,         // { creditCardNumber, expirationDate, cvvCode, cardHolderName }
  setPayment,
  shipping,        // { name, email, addressLine1, addressLine2, city, state, zip }
  setShipping,
  resetOrder,      // clears everything after the order is placed
} = useOrder()
```

The cart is also saved to `localStorage`, so it survives a page refresh.

## Styling

- **Colors** – use the variables in `src/index.css` (`--ink`, `--muted`, `--accent`, `--border`) instead of new hex codes.
- **Prices** – always use `formatPrice()` from `src/utils/format.js`.
- Styles live in `src/App.css`, grouped under a comment per page or component.

## Other files

- `src/components/Header.jsx` / `Cart.jsx` / `Footer.jsx` – top bar, slide-out cart, and footer (on every page)
- `src/components/ProductPreview.jsx` – product photo popup with a quantity picker
- `src/components/ScrollManager.jsx` – scrolls to the top on page changes and restores position on back/forward
- `public/images/` – hero photo and illustrations (product photos are served from S3 via the inventory API)
