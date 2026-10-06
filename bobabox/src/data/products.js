// Hardcoded catalog for Lab 5. This moves to the backend in Labs 7-8.
// gradient is the CSS background for each kit's color swatch.
// image (optional) is a product photo in /public/images shown on top of the swatch.

const products = [
  {
    id: 1,
    name: 'Strawberry Milk Tea Kit',
    description: 'Real strawberry purée, black tea, and tapioca pearls. Makes 6 drinks.',
    price: 22.49,
    gradient: 'radial-gradient(circle at 30% 25%, #fff0f5 0%, #ff7aa8 25%, #ff1f6b 55%, #b0003a 85%, #5c0020 100%)',
  },
  {
    id: 2,
    name: 'Taro Milk Tea Kit',
    description: 'Real taro powder, jasmine tea, and tapioca pearls. Makes 6 drinks.',
    price: 23.99,
    gradient:
      'linear-gradient(135deg, #12043a 5%, #5b2bd6 38%, #e6d4ff 50%, #7c4dff 60%, #1e0b4f 95%)',
  },
  {
    id: 3,
    name: 'Brown Sugar Boba Kit',
    description: 'Slow-cooked brown sugar syrup and tapioca pearls. Just add milk. Makes 6 drinks.',
    price: 24.99,
    gradient:
      'radial-gradient(circle at 30% 25%, rgba(255, 255, 255, 0.55), transparent 40%), linear-gradient(155deg, #fff1dc 0%, #f7d9b0 18%, #7a3b10 30%, #f0c48c 42%, #4a2108 55%, #e2a868 68%, #2b1407 85%)',
  },
  {
    id: 4,
    name: 'Matcha Latte Kit',
    description: 'Ceremonial-grade matcha, cane syrup, and tapioca pearls. Makes 6 drinks.',
    price: 26.99,
    gradient: 'radial-gradient(circle at 35% 30%, #f4ff9e 0%, #c6f04d 30%, #6fa82a 65%, #1f3d10 100%)',
  },
  {
    id: 5,
    name: 'Mango Green Tea Kit',
    description: 'Jasmine green tea, mango syrup, and popping boba. Makes 6 drinks.',
    price: 22.99,
    gradient:
      'radial-gradient(circle at 30% 30%, #fff59d 0%, #ffc107 25%, #ff7a1a 50%, #e53935 75%, #7a1010 100%)',
  },
]

export default products
