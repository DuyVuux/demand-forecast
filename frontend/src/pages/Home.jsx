import React from 'react';
import { Link } from 'react-router-dom';
import styles from './Home.module.css';

const features = [
  {
    title: 'Data Analysis',
    description: 'Upload your dataset to get an in-depth analysis of data quality, column distributions, and correlations.',
    path: '/data-analysis',
    icon: '📊',
  },
  {
    title: 'Product-Customer Forecast',
    description: 'Forecast future demand based on historical data for specific product and customer segments.',
    path: '/pc-forecast',
    icon: '🏭',
  },
  {
    title: 'SKU Forecast',
    description: 'Generate demand forecasts for individual Stock Keeping Units (SKUs) to optimize inventory.',
    path: '/sku-forecast',
    icon: '📦',
  },
];

const Home = () => {
  return (
    <div className={styles.homeContainer}>
      <header className={styles.header}>
        <h1>Welcome to the Demand Forecasting Portal</h1>
        <p>Your one-stop solution for analyzing historical data and predicting future demand.</p>
      </header>
      <div className={styles.featuresGrid}>
        {features.map((feature) => (
          <Link to={feature.path} key={feature.title} className={styles.featureCard}>
            <div className={styles.cardIcon}>{feature.icon}</div>
            <h3>{feature.title}</h3>
            <p>{feature.description}</p>
            <div className={styles.cardAction}>
              Go to {feature.title.split(' ')[0]} →
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default Home;
