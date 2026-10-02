import { Link } from 'react-router-dom'

const VALUES = [
  {
    title: 'Community First',
    text: 'We are here for students, alumni, families, and fans. Anyone who has ever felt at home on campus belongs with us.',
  },
  {
    title: 'Comfort That Lasts',
    text: 'Soft fleece, sturdy knits, and classic cuts made to survive finals week, chilly tailgates, and many reunions to come.',
  },
  {
    title: 'Pride in Every Stitch',
    text: 'From your residential college crest to your favorite varsity sport, every design celebrates a piece of the Bulldog story.',
  },
]

export default function About() {
  return (
    <>
      <section className="page-hero">
        <p className="eyebrow">About Us</p>
        <h1>Made by Bulldogs, for Bulldogs 🐾</h1>
        <p className="hero-sub">
          Campus Customs started with a simple idea: the best memories happen in your favorite
          sweatshirt. So we set out to make gear that feels as good as the moments you wear it to.
        </p>
      </section>

      <section className="section about-story">
        <h2>Our Story</h2>
        <p>
          Think about the walk across Old Campus on a crisp fall morning, the roar of the crowd when
          the Bulldogs take the field, or the late-night pizza run with your suitemates. Those moments
          deserve something special to wear, and that's where we come in.
        </p>
        <p>
          We bring together game-day classics, residential college favorites, and cozy everyday
          staples so you can show your colors wherever life takes you. Whether you're a first-year
          finding your people, a proud parent at Family Weekend, or an alum heading back for
          Homecoming, there's a little blue here with your name on it.
        </p>
      </section>

      <section className="section">
        <div className="highlights">
          {VALUES.map((v) => (
            <div key={v.title} className="highlight">
              <h3>{v.title}</h3>
              <p>{v.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="banner">
          <h2>Come Join the Cheering Section!</h2>
          <p>Find your new favorite piece and wear your pride loud.</p>
          <Link to="/products" className="btn btn-light btn-lg">Browse Products</Link>
        </div>
      </section>
    </>
  )
}
