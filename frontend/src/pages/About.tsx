import { Link } from 'react-router-dom'
import DanTheBulldog from '../components/DanTheBulldog'

const VALUES = [
  {
    title: 'Community first',
    text: 'For students, alumni, families, and fans. Anyone who has ever felt at home on campus belongs here.',
  },
  {
    title: 'Comfort that lasts',
    text: 'Soft fleece, sturdy knits, and classic cuts made to survive finals week, chilly tailgates, and many reunions to come.',
  },
  {
    title: 'Pride in every stitch',
    text: 'From your residential college crest to your favorite varsity sport, every design tells a piece of the Bulldog story.',
  },
]

export default function About() {
  return (
    <>
      <section className="page-intro">
        <span className="eyebrow">About us</span>
        <h1>Made by Bulldogs, for Bulldogs.</h1>
        <p className="lead">
          Campus Customs started with a simple idea: the best memories happen in your favorite
          sweatshirt. So we set out to make gear that feels as good as the moments you wear it to.
        </p>
      </section>

      <section className="section">
        <div className="story">
          <h2>Our story</h2>
          <div className="story-body">
            <p>
              Picture the walk across Old Campus on a crisp fall morning, the roar of the crowd when
              the Bulldogs take the field, or the late-night pizza run with your suitemates. Those
              moments deserve something special to wear, and that's where we come in.
            </p>
            <p>
              We bring together game-day classics, residential college favorites, and cozy everyday
              staples so you can show your colors wherever life takes you. Whether you're a first-year
              finding your people, a proud parent at Family Weekend, or an alum heading back for
              Homecoming, there's something here with your name on it.
            </p>
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

      <section className="dan-band">
        <div className="dan-band-inner">
          <DanTheBulldog className="dan" />
          <div>
            <span className="eyebrow">Our mascot</span>
            <h2>Say hello to Dan</h2>
            <p>
              Every great team needs a bulldog. Dan is loyal, a little stubborn, and fiercely proud of
              his school, just like the rest of us. He keeps an eye on the shop, greets every visitor,
              and never says no to a cozy crewneck.
            </p>
            <Link to="/products" className="btn btn-primary">Shop with Dan</Link>
          </div>
        </div>
      </section>
    </>
  )
}
