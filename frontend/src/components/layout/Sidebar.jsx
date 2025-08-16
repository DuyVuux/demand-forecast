import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import styles from './Sidebar.module.css';

const Sidebar = () => {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.logoContainer}>
        <Link to="/" className={styles.logo}>
          DemandTTC
        </Link>
      </div>
      <nav className={styles.navList}>
        <li className={styles.navItem}>
          <NavLink to="/data-analysis" className={({ isActive }) => isActive ? `${styles.link} ${styles.active}` : styles.link}>
            <span className={styles.navIcon}>📊</span> Data Analysis
          </NavLink>
        </li>
        <li className={styles.navItem}>
          <NavLink to="/pc-forecast" className={({ isActive }) => isActive ? `${styles.link} ${styles.active}` : styles.link}>
            <span className={styles.navIcon}>🏭</span> PC Forecast
          </NavLink>
        </li>
        <li className={styles.navItem}>
          <NavLink to="/sku-forecast" className={({ isActive }) => isActive ? `${styles.link} ${styles.active}` : styles.link}>
            <span className={styles.navIcon}>📦</span> SKU Forecast
          </NavLink>
        </li>
      </nav>
    </aside>
  );
};

export default Sidebar;
