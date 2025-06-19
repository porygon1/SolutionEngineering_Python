import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  MagnifyingGlassIcon, 
  UserCircleIcon,
  BellIcon,
  ChevronDownIcon 
} from '@heroicons/react/24/outline';
import { Menu, Transition } from '@headlessui/react';

const Navbar: React.FC = () => {
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Implement search functionality
    console.log('Searching for:', searchQuery);
  };

  return (
    <nav className="bg-spotify-darkgray/95 backdrop-blur-md border-b border-spotify-gray/20 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left side - Navigation */}
          <div className="flex items-center space-x-6">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-spotify rounded-full flex items-center justify-center">
                <span className="text-spotify-white font-bold text-sm">🎵</span>
              </div>
              <span className="text-spotify-white font-bold text-lg hidden sm:block">
                MusicAI
              </span>
            </Link>

            {/* Navigation Links */}
            <div className="hidden md:flex space-x-6">
              <NavLink to="/" active={location.pathname === '/'}>
                Home
              </NavLink>
              <NavLink to="/preferences" active={location.pathname === '/preferences'}>
                Preferences
              </NavLink>
              <NavLink to="/recommendations" active={location.pathname === '/recommendations'}>
                Recommendations
              </NavLink>
              <NavLink to="/explore" active={location.pathname === '/explore'}>
                Explore
              </NavLink>
            </div>
          </div>

          {/* Center - Search */}
          <div className="flex-1 max-w-md mx-4">
            <form onSubmit={handleSearch} className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5 text-spotify-lightgray" />
              </div>
              <input
                type="text"
                placeholder="Search for songs, artists..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-spotify-gray text-spotify-white placeholder-spotify-lightgray rounded-full border-none focus:outline-none focus:ring-2 focus:ring-spotify-green focus:bg-spotify-hover transition-colors"
              />
            </form>
          </div>

          {/* Right side - User menu */}
          <div className="flex items-center space-x-4">
            {/* Notifications */}
            <button className="p-2 text-spotify-lightgray hover:text-spotify-white transition-colors">
              <BellIcon className="h-6 w-6" />
            </button>

            {/* User menu */}
            <Menu as="div" className="relative">
              <Menu.Button className="flex items-center space-x-2 p-2 rounded-full hover:bg-spotify-gray transition-colors">
                <UserCircleIcon className="h-8 w-8 text-spotify-lightgray" />
                <ChevronDownIcon className="h-4 w-4 text-spotify-lightgray" />
              </Menu.Button>

              <Transition
                enter="transition ease-out duration-200"
                enterFrom="transform opacity-0 scale-95"
                enterTo="transform opacity-100 scale-100"
                leave="transition ease-in duration-75"
                leaveFrom="transform opacity-100 scale-100"
                leaveTo="transform opacity-0 scale-95"
              >
                <Menu.Items className="absolute right-0 mt-2 w-48 bg-spotify-gray rounded-md shadow-spotify border border-spotify-lightgray/20 focus:outline-none">
                  <div className="py-1">
                    <Menu.Item>
                      {({ active }: { active: boolean }) => (
                        <a
                          href="#"
                          className={`block px-4 py-2 text-sm ${
                            active ? 'bg-spotify-hover text-spotify-white' : 'text-spotify-lightgray'
                          }`}
                        >
                          Profile
                        </a>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }: { active: boolean }) => (
                        <a
                          href="#"
                          className={`block px-4 py-2 text-sm ${
                            active ? 'bg-spotify-hover text-spotify-white' : 'text-spotify-lightgray'
                          }`}
                        >
                          Settings
                        </a>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }: { active: boolean }) => (
                        <a
                          href="#"
                          className={`block px-4 py-2 text-sm ${
                            active ? 'bg-spotify-hover text-spotify-white' : 'text-spotify-lightgray'
                          }`}
                        >
                          Sign out
                        </a>
                      )}
                    </Menu.Item>
                  </div>
                </Menu.Items>
              </Transition>
            </Menu>
          </div>
        </div>
      </div>
    </nav>
  );
};

// NavLink component for active state styling
interface NavLinkProps {
  to: string;
  active: boolean;
  children: React.ReactNode;
}

const NavLink: React.FC<NavLinkProps> = ({ to, active, children }) => (
  <Link
    to={to}
    className={`relative px-3 py-2 text-sm font-medium transition-colors ${
      active
        ? 'text-spotify-white'
        : 'text-spotify-lightgray hover:text-spotify-white'
    }`}
  >
    {children}
    {active && (
      <motion.div
        layoutId="navbar-indicator"
        className="absolute bottom-0 left-0 right-0 h-0.5 bg-spotify-green"
        initial={false}
      />
    )}
  </Link>
);

export default Navbar; 