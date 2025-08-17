import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark', // Sử dụng theme tối để dễ dàng có nền navy
    primary: {
      main: '#58A6FF', // Một màu xanh dương sáng cho các element chính
    },
    background: {
      default: '#0D1117', // Màu nền xanh navy đậm
      paper: '#161B22',   // Màu nền cho các component như Card, Paper
    },
    text: {
      primary: '#C9D1D9', // Màu chữ chính (trắng ngà)
      secondary: '#8B949E', // Màu chữ phụ
    },
  },
  typography: {
    fontFamily: 'Arial, Helvetica, sans-serif',
    h1: { fontSize: '2.5rem', fontWeight: 600 },
    h2: { fontSize: '2rem', fontWeight: 600 },
    h3: { fontSize: '1.75rem', fontWeight: 600 },
    h4: { fontSize: '1.5rem', fontWeight: 500 },
    body1: { fontSize: '1rem' },
    button: {
      textTransform: 'none', // Giữ nguyên case của chữ trong button
      fontWeight: 600,
    },
  },
  spacing: 8, // Hệ số spacing cơ bản là 8px
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8, // Bo góc button
          transition: 'background-color 0.3s ease, transform 0.2s ease',
          '&:hover': {
            transform: 'translateY(-2px)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          transition: 'box-shadow 0.3s ease',
          '&:hover': {
            boxShadow: '0px 10px 20px rgba(0, 0, 0, 0.2)',
          }
        }
      }
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: '#22272E',
          color: '#C9D1D9',
          border: '1px solid #30363D',
        },
        arrow: {
          color: '#22272E',
        }
      }
    }
  },
});

export default theme;
