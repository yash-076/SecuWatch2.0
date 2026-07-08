import { Link } from 'react-router-dom'
import {
  Shield,
  Activity,
  MonitorSmartphone,
  BarChart3,
  Wifi,
  Users,
  ArrowRight,
  ChevronRight,
  Zap,
  Lock,
  Eye,
} from 'lucide-react'

const features = [
  {
    icon: Activity,
    title: 'Real-Time Alert Monitoring',
    description:
      'Receive and triage security alerts instantly via WebSocket streaming. Every threat surfaces the moment it occurs.',
  },
  {
    icon: MonitorSmartphone,
    title: 'Device Management',
    description:
      'Register, configure, and monitor all network devices from a single pane. Track heartbeats, status, and OS info.',
  },
  {
    icon: Shield,
    title: 'Severity-Based Triage',
    description:
      'Color-coded severity levels — Critical, High, Medium, Low — let analysts focus on what matters most.',
  },
  {
    icon: BarChart3,
    title: 'Analytics Dashboard',
    description:
      'Visualize alert trends, severity distributions, and top threat sources with interactive charts and metrics.',
  },
  {
    icon: Wifi,
    title: 'WebSocket Live Streaming',
    description:
      'Persistent WebSocket connection delivers alerts the instant they are generated. No polling, no delays.',
  },
  {
    icon: Users,
    title: 'Role-Based Access Control',
    description:
      'Analysts and admins get scoped permissions. Assign alerts, manage teams, and enforce accountability.',
  },
]

const steps = [
  {
    number: '01',
    icon: Users,
    title: 'Register Your Organization',
    description: 'Create an account, set up your organization, and invite your security team.',
  },
  {
    number: '02',
    icon: MonitorSmartphone,
    title: 'Connect Your Devices',
    description: 'Register devices (Windows, Linux, Web) and configure heartbeat & log intervals.',
  },
  {
    number: '03',
    icon: Eye,
    title: 'Monitor & Respond',
    description: 'Watch threats arrive in real-time, triage by severity, assign to analysts, and resolve.',
  },
]

const techStack = [
  { name: 'React', description: 'Frontend UI' },
  { name: 'FastAPI', description: 'Backend API' },
  { name: 'WebSocket', description: 'Live Streaming' },
  { name: 'Tailwind CSS', description: 'Styling' },
  { name: 'Recharts', description: 'Data Visualization' },
  { name: 'JWT Auth', description: 'Security' },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-soc-bg text-soc-text overflow-hidden">
      {/* ========== NAVBAR ========== */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-soc-border bg-soc-bg/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 bg-gradient-to-br from-soc-accent to-soc-accent-light rounded-lg flex items-center justify-center shadow-soc-glow group-hover:shadow-soc-glow-strong transition-all duration-300">
              <Shield size={18} className="text-white" />
            </div>
            <span className="font-bold text-lg text-soc-text tracking-tight">
              Secu<span className="text-soc-accent">Watch</span>
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm text-soc-secondary hover:text-soc-text transition-smooth">
              Features
            </a>
            <a href="#how-it-works" className="text-sm text-soc-secondary hover:text-soc-text transition-smooth">
              How It Works
            </a>
            <a href="#tech" className="text-sm text-soc-secondary hover:text-soc-text transition-smooth">
              Tech Stack
            </a>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="px-4 py-2 text-sm text-soc-secondary hover:text-soc-text border border-soc-border rounded-lg hover:border-soc-accent/30 transition-smooth"
            >
              Login
            </Link>
            <Link
              to="/signup"
              className="px-5 py-2 text-sm font-medium text-white bg-gradient-to-r from-soc-accent to-soc-accent-light rounded-lg hover:shadow-soc-glow transition-all duration-300"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* ========== HERO ========== */}
      <section className="relative min-h-screen flex items-center justify-center pt-16 bg-grid-pattern">
        {/* Glow orbs */}
        <div className="hero-glow" style={{ top: '-10%', left: '15%' }} />
        <div className="hero-glow" style={{ bottom: '-20%', right: '10%', width: '500px', height: '500px' }} />

        <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-soc-accent/20 bg-soc-accent/5 text-soc-accent text-xs font-medium mb-8 animate-fade-up opacity-0">
            <Zap size={14} />
            SOC-Grade Security Monitoring
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold leading-tight mb-6 animate-fade-up opacity-0 stagger-1">
            Real-Time Cybersecurity.
            <br />
            <span className="gradient-text">Simplified.</span>
          </h1>

          <p className="text-lg md:text-xl text-soc-secondary max-w-2xl mx-auto mb-10 animate-fade-up opacity-0 stagger-2 leading-relaxed">
            Monitor threats, manage devices, and analyze security alerts with a
            professional SOC-grade dashboard — all in real-time.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-up opacity-0 stagger-3">
            <Link
              to="/signup"
              className="group flex items-center gap-2 px-8 py-3.5 text-base font-semibold text-white bg-gradient-to-r from-soc-accent to-soc-accent-light rounded-xl hover:shadow-soc-glow-strong transition-all duration-300"
            >
              Get Started Free
              <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              to="/login"
              className="group flex items-center gap-2 px-8 py-3.5 text-base font-medium text-soc-text border border-soc-border rounded-xl hover:border-soc-accent/30 hover:bg-soc-card transition-all duration-300"
            >
              Login to Dashboard
              <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>

          {/* Stats row */}
          <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8 animate-fade-up opacity-0 stagger-4">
            {[
              { value: 'Real-Time', label: 'Alert Streaming' },
              { value: '5', label: 'Severity Levels' },
              { value: '3', label: 'Device Types' },
              { value: 'RBAC', label: 'Access Control' },
            ].map((stat, i) => (
              <div key={i} className="text-center">
                <p className="text-2xl md:text-3xl font-bold text-soc-text landing-stat">{stat.value}</p>
                <p className="text-xs text-soc-muted mt-1 uppercase tracking-wider">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== FEATURES ========== */}
      <section id="features" className="py-24 md:py-32 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-soc-accent text-sm font-semibold uppercase tracking-widest mb-3">Core Capabilities</p>
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Everything You Need for <span className="gradient-text">Threat Monitoring</span>
            </h2>
            <p className="text-soc-secondary max-w-2xl mx-auto">
              Built from the ground up for security operations — every feature serves a real purpose in your incident response workflow.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <div
                key={i}
                className={`card-glass card-hover-glow p-8 transition-all duration-500 hover:-translate-y-1 animate-fade-up opacity-0 stagger-${i + 1}`}
              >
                <div className="w-12 h-12 rounded-xl bg-soc-accent/10 flex items-center justify-center mb-5">
                  <feature.icon size={24} className="text-soc-accent" />
                </div>
                <h3 className="text-lg font-semibold text-soc-text mb-3">{feature.title}</h3>
                <p className="text-sm text-soc-secondary leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== HOW IT WORKS ========== */}
      <section id="how-it-works" className="py-24 md:py-32 bg-grid-pattern relative">
        <div className="hero-glow" style={{ top: '20%', right: '-10%', width: '400px', height: '400px' }} />

        <div className="max-w-6xl mx-auto px-6 relative z-10">
          <div className="text-center mb-16">
            <p className="text-soc-accent text-sm font-semibold uppercase tracking-widest mb-3">Get Started</p>
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Three Steps to <span className="gradient-text">Full Visibility</span>
            </h2>
            <p className="text-soc-secondary max-w-xl mx-auto">
              From registration to real-time monitoring in minutes.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {steps.map((step, i) => (
              <div key={i} className="relative group">
                {/* Connector line */}
                {i < steps.length - 1 && (
                  <div className="hidden md:block absolute top-12 left-[60%] w-full h-px bg-gradient-to-r from-soc-accent/30 to-transparent" />
                )}
                <div className="card-glass p-8 text-center transition-all duration-500 hover:-translate-y-1">
                  <div className="text-5xl font-black text-soc-accent/10 mb-4 select-none">{step.number}</div>
                  <div className="w-14 h-14 rounded-2xl bg-soc-accent/10 flex items-center justify-center mx-auto mb-5 group-hover:bg-soc-accent/20 transition-colors duration-300">
                    <step.icon size={28} className="text-soc-accent" />
                  </div>
                  <h3 className="text-lg font-semibold text-soc-text mb-3">{step.title}</h3>
                  <p className="text-sm text-soc-secondary leading-relaxed">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== TECH STACK ========== */}
      <section id="tech" className="py-24 md:py-32 relative">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-soc-accent text-sm font-semibold uppercase tracking-widest mb-3">Built With</p>
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Modern <span className="gradient-text">Tech Stack</span>
            </h2>
            <p className="text-soc-secondary max-w-xl mx-auto">
              Production-ready technologies powering a professional security dashboard.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {techStack.map((tech, i) => (
              <div
                key={i}
                className="card-glass p-5 text-center hover:-translate-y-1 transition-all duration-300"
              >
                <p className="text-sm font-semibold text-soc-text mb-1">{tech.name}</p>
                <p className="text-xs text-soc-muted">{tech.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== CTA ========== */}
      <section className="py-24 md:py-32 relative">
        <div className="hero-glow" style={{ top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }} />

        <div className="max-w-3xl mx-auto px-6 text-center relative z-10">
          <div className="card-glass p-12 md:p-16 animate-glow-pulse">
            <Lock size={40} className="text-soc-accent mx-auto mb-6" />
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Ready to Secure Your Infrastructure?
            </h2>
            <p className="text-soc-secondary mb-8 max-w-lg mx-auto">
              Connect your devices to SecuWatch and get real-time visibility into threats across your entire network.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/signup"
                className="group flex items-center gap-2 px-8 py-3.5 text-base font-semibold text-white bg-gradient-to-r from-soc-accent to-soc-accent-light rounded-xl hover:shadow-soc-glow-strong transition-all duration-300"
              >
                Create Free Account
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                to="/login"
                className="px-8 py-3.5 text-base font-medium text-soc-text border border-soc-border rounded-xl hover:border-soc-accent/30 transition-all duration-300"
              >
                Login
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ========== FOOTER ========== */}
      <footer className="border-t border-soc-border py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-soc-accent to-soc-accent-light rounded-lg flex items-center justify-center">
                <Shield size={16} className="text-white" />
              </div>
              <span className="font-bold text-soc-text">
                Secu<span className="text-soc-accent">Watch</span>
              </span>
            </div>

            <p className="text-sm text-soc-muted text-center">
              SOC-grade cybersecurity monitoring dashboard. Built for security teams.
            </p>

            <p className="text-xs text-soc-muted">
              &copy; {new Date().getFullYear()} SecuWatch. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
