import React from 'react';

const Home: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl md:text-6xl font-bold bg-gradient-spotify bg-clip-text text-transparent">
          Discover Your Next
        </h1>
        <h1 className="text-4xl md:text-6xl font-bold text-spotify-white">
          Favorite Song
        </h1>
        <p className="text-xl text-spotify-lightgray max-w-2xl mx-auto">
          AI-powered music recommendations using advanced clustering and machine learning
        </p>
      </div>

      {/* Stats Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="Songs Analyzed"
          value="101,939"
          description="Tracks in our database"
          icon="🎵"
        />
        <StatCard
          title="Music Clusters"
          value="61"
          description="Distinct musical groups"
          icon="🎯"
        />
        <StatCard
          title="Recommendations"
          value="∞"
          description="Personalized for you"
          icon="✨"
        />
      </div>

      {/* Quick Actions */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-spotify-white">Get Started</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ActionCard
            title="Set Your Preferences"
            description="Tell us what music you like to get better recommendations"
            action="Set Preferences"
            href="/preferences"
          />
          <ActionCard
            title="Explore Clusters"
            description="Discover new music by exploring different musical clusters"
            action="Explore Music"
            href="/explore"
          />
        </div>
      </div>
    </div>
  );
};

interface StatCardProps {
  title: string;
  value: string;
  description: string;
  icon: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, description, icon }) => (
  <div className="bg-spotify-gray rounded-lg p-6 hover:bg-spotify-hover transition-colors">
    <div className="flex items-center space-x-3">
      <span className="text-2xl">{icon}</span>
      <div>
        <h3 className="text-lg font-semibold text-spotify-white">{title}</h3>
        <p className="text-2xl font-bold text-spotify-green">{value}</p>
        <p className="text-sm text-spotify-lightgray">{description}</p>
      </div>
    </div>
  </div>
);

interface ActionCardProps {
  title: string;
  description: string;
  action: string;
  href: string;
}

const ActionCard: React.FC<ActionCardProps> = ({ title, description, action, href }) => (
  <div className="bg-spotify-gray rounded-lg p-6 hover:bg-spotify-hover transition-colors group">
    <h3 className="text-lg font-semibold text-spotify-white mb-2">{title}</h3>
    <p className="text-spotify-lightgray mb-4">{description}</p>
    <a
      href={href}
      className="inline-flex items-center px-4 py-2 bg-spotify-green text-spotify-black font-medium rounded-full hover:bg-spotify-lightgreen transition-colors"
    >
      {action}
    </a>
  </div>
);

export default Home; 