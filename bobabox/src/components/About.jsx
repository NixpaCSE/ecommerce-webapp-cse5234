import { Link } from 'react-router-dom'
import { FiArrowRight } from 'react-icons/fi'
import Bubbles from './Bubbles.jsx'

const executives = [
  {
    name: 'Nicholas Pappas',
    title: 'CEO and President',
    image: '/images/nicholas-pappas.jpg',
    imagePosition: 'center 18%',
    blurb:
      'Nicholas runs boba.box from the product promise down to the business case. He treats every kit like it has to earn its place, and he measures success by the value it creates for the people who count on it.',
    education: 'Computer Science and Engineering, The Ohio State University',
    experience: 'Software Engineer at JPMorgan Chase',
    passion: 'Providing business value to stakeholders',
  },
  {
    name: 'Jerry Chang',
    title: 'Chief AI Officer',
    image: '/images/jerry-chang.jpg',
    imagePosition: 'center 22%',
    blurb:
      'Jerry is the reason this store has a point of view on AI. He designs agents that can recommend a kit, answer a question, and keep the shopping experience sharp without making it complicated.',
    education: 'Computer Science and Engineering, The Ohio State University',
    experience: 'Software Engineer at JPMorgan Chase',
    passion: 'Developing AI agents',
  },
  {
    name: 'Yukun Wang',
    title: 'Chief Information Officer',
    image: '/images/yukun-wang.jpg',
    imagePosition: 'center 18%',
    blurb: 'Yukun is the person to call for any and all software issues at the store site. Taught himself coding at the age of 3, his programming prowess has been honed over the years before landing a job at an online boba shop.',
    education: 'Computer Science and Engineering, The Ohio State University',
    experience: 'Software Engineer at Winbond',
    passion: 'Developing the next best invention second only to the wheel.',
  },
]

function About() {
  return (
    <section className="about">
      <div className="hero">
        <Bubbles />
        <h1 className="hero-title">about us</h1>
        <div className="hero-row">
          <FiArrowRight className="hero-arrow" aria-hidden="true" />
          <p className="hero-text">
            Café-quality boba, boxed and delivered. Built by a team that cares how the drink — and the business — turns out.
          </p>
        </div>
      </div>

      <div className="about-intro">
        <article className="about-card">
          <span className="about-kicker">Mission</span>
          <h2>boba worth making at home</h2>
          <p>
            Bring a real café drink to the kitchen. Every kit ships with tea, syrups, and tapioca pearls so you can make six drinks in about ten minutes — no line, no drive, no guesswork.
          </p>
        </article>

        <article className="about-card">
          <span className="about-kicker">Vision</span>
          <h2>the best cup is the one you made</h2>
          <p>
            We want boba.box to be the kit people reach for when they want the drink they already love. One box at the door, and a cup that tastes like it came from the café.
          </p>
        </article>
      </div>

      <article className="about-strategy">
        <span className="about-kicker">Strategy</span>
        <h2>online only, on purpose</h2>
        <p>
          We keep the catalog small and sell it direct. Five flavors we would order ourselves, packed as complete kits, priced so a week of drinks costs less than a week of café runs. We grow by making the next order obvious: better recipes, clearer kits, and service that treats every customer like a stakeholder.
        </p>
      </article>

      <h2 className="about-section-title">meet our executives</h2>
      <div className="exec-grid">
        {executives.map((person) => (
          <article key={person.name} className="exec-card">
            <img
              className="exec-photo"
              src={person.image}
              alt={`Portrait of ${person.name}`}
              style={{ objectPosition: person.imagePosition }}
            />

            <div className="exec-body">
              <h3>{person.name}</h3>
              <p className={`exec-title ${person.title === 'Coming soon' ? 'is-placeholder' : ''}`}>
                {person.title}
              </p>
              <p className="exec-blurb">{person.blurb}</p>
              <dl className="exec-facts">
                <div>
                  <dt>Education</dt>
                  <dd>{person.education}</dd>
                </div>
                <div>
                  <dt>Experience</dt>
                  <dd>{person.experience}</dd>
                </div>
                <div>
                  <dt>Passion</dt>
                  <dd>{person.passion}</dd>
                </div>
              </dl>
            </div>
          </article>
        ))}
      </div>

      <div className="about-cta">
        <Link to="/purchase" className="primary-button">
          shop the kits <FiArrowRight />
        </Link>
      </div>
    </section>
  )
}

export default About
