import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, type Product } from '../api'
import ProductCard from '../components/ProductCard'
import DanTheBulldog from '../components/DanTheBulldog'

const FEATURED_IDS = [
  '2025-yale-vs-harvard-t-shirt',
  'baseball-left-chest-crewneck',
  'champion-reverse-weave-hoodie-1',
  'davenport-college-crewneck',
]

const VALUES = [
  {
    title: 'Game day, every day',
    text: 'From The Game to Friday night hockey, show up proud and ready to cheer.',
  },
  {
    title: 'Your college, your crew',
    text: 'Rep your residential college or your school: Davenport, Morse, Law, Art, and more.',
  },
  {
    title: 'The whole Bulldog family',
    text: 'Mom, Dad, Grandpa, little brother. Everyone gets a spot in the cheering section.',
  },
]

export default function Home() {
  const [featured, setFeatured] = useState<Product[]>([])

  useEffect(() => {
    fetchProducts()
      .then((all) => {
        const picks = FEATURED_IDS.map((id) => all.find((p) => p.product_id === id)).filter(
          (p): p is Product => Boolean(p),
        )
        setFeatured(picks.length ? picks : all.slice(0, 4))
      })
      .catch(() => setFeatured([]))
  }, [])

  return (
    <>
      <section className="hero">
        <div>
          <span className="eyebrow">Welcome home, Bulldogs</span>
          <h1>
            Bulldog pride, <em>made for every day.</em>
          </h1>
          <p className="lead">
            Cozy crewnecks, game-day tees, and hoodies built for late-night study sessions. Campus
            Customs is where New Haven spirit meets everyday comfort, and we saved you a seat.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-primary btn-lg">Shop the collection</Link>
            <Link to="/about" className="btn btn-ghost btn-lg">Our story</Link>
          </div>
        </div>
        <div className="hero-art">
          <div className="hero-circle">
            <DanTheBulldog className="dan" />
          </div>
          <div className="hero-badge">
            <strong>Hi, I'm Dan!</strong> Chief comfort officer.
          </div>
        </div>
      </section>

      <section className="section section-tight">
        <div className="values">
          {VALUES.map((v, i) => (
            <div key={v.title} className="value">
              <div className="value-num">0{i + 1}</div>
              <h3>{v.title}</h3>
              <p>{v.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <span className="eyebrow">Fresh picks</span>
            <h2>Favorites for the season</h2>
          </div>
          <Link to="/products" className="link-arrow">View all products →</Link>
        </div>
        <div className="product-grid">
          {featured.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      </section>

      <section className="dan-band">
        <div className="dan-band-inner">
          <DanTheBulldog className="dan" />
          <div>
            <span className="eyebrow">Meet Dan</span>
            <h2>Your new shopping buddy</h2>
            <p>
              Dan knows every hoodie, every size, and exactly what's in stock. Click his face in the
              corner to say hello. He's warming up on the sidelines and will be ready to help you
              find the perfect fit very soon.
            </p>
          </div>
        </div>
      </section>
    </>
  )
}
