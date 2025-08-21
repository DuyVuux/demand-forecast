import { createTheme } from '@mui/material/styles';

// Light Theme Definition
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#001f3f', // Navy blue for main actions and links
    },
    background: {
      default: '#ffffff', // Main background: white
      paper: '#ffffff',   // Card, table, chart background: white
    },
    text: {
      primary: '#212121', // Primary text: almost black for readability
      secondary: '#757575', // Secondary text: dark grey
    },
  },
  typography: {
    fontFamily: 'Arial, Helvetica, sans-serif',
    fontSize: 14,
    h1: { fontSize: '2.2rem', fontWeight: 600 },
    h2: { fontSize: '1.8rem', fontWeight: 600 },
    h3: { fontSize: '1.5rem', fontWeight: 600 },
    h4: { fontSize: '1.2rem', fontWeight: 500 },
    body1: { fontSize: '1rem' }, // 16px
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  spacing: 8, // Base spacing unit: 8px
  components: {
    // Button Overrides
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
          transition: 'background-color 0.2s ease-in-out, transform 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-1px)',
            boxShadow: '0 4px 12px rgba(0, 31, 63, 0.2)',
          },
        },
      },
    },
    // Card and Paper Overrides
    MuiPaper: {
      styleOverrides: {
        root: {
          border: '1px solid #e0e0e0', // Light grey border
          borderRadius: 12,
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          transition: 'box-shadow 0.3s ease',
        }
      }
    },
    // Link Overrides
    MuiLink: {
      styleOverrides: {
        root: {
          color: '#001f3f', // Navy blue
          transition: 'color 0.2s ease-in-out',
          '&:hover': {
            textDecoration: 'underline',
            color: '#004080', // Slightly lighter navy on hover
          },
        },
      },
    },
    // Table Overrides
    MuiTableCell: {
        styleOverrides: {
            root: {
                borderBottom: '1px solid #e0e0e0', // Consistent border for table cells
            }
        }
    },
    // Tooltip Overrides
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: '#001f3f', // Navy background
          color: '#ffffff',
          border: '1px solid #001f3f',
        },
        arrow: {
          color: '#001f3f',
        }
      }
    }
  },
});

export default theme;
