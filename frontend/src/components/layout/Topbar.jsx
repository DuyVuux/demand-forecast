import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import styles from './Topbar.module.css';

const Topbar = () => {
  const [language, setLanguage] = useState('EN');

  const toggleLanguage = () => {
    setLanguage(prev => (prev === 'EN' ? 'VN' : 'EN'));
  };

  return (
    <header className={styles.topbar}>
      <Link to="/" className={styles.homeButton}>Home</Link>
      <div className={styles.languageSwitcher} onClick={toggleLanguage} title="Change Language">
        <button className={language === 'EN' ? styles.active : ''}>EN</button>
        <span>/</span>
        <button className={language === 'VN' ? styles.active : ''}>VN</button>
      </div>
    </header>
  );
};

export default Topbar;
