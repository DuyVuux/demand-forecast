import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardActionArea,
  CardContent,
  useTheme,
  Paper,
  Button
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  Factory as FactoryIcon,
  Inventory2 as SkuIcon,
  ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';

const features = [
  {
    title: 'Data Analysis',
    description: 'Tải lên bộ dữ liệu của bạn để phân tích chuyên sâu về chất lượng dữ liệu, phân phối và các mối tương quan.',
    path: '/data-analysis',
    icon: <AnalyticsIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
  },
  {
    title: 'Product-Customer Forecast',
    description: 'Dự báo nhu cầu cho các phân khúc sản phẩm-khách hàng cụ thể dựa trên dữ liệu lịch sử.',
    path: '/pc-forecast',
    icon: <FactoryIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
  },
  {
    title: 'SKU Forecast',
    description: 'Tạo dự báo nhu cầu cho từng SKU riêng lẻ để tối ưu hóa hàng tồn kho và lập kế hoạch.',
    path: '/sku-forecast',
    icon: <SkuIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
  },
];

const Home = () => {
  const navigate = useNavigate();
  const theme = useTheme();

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ textAlign: 'center', mb: 6 }}>
        <img src="/images/logo_smartlog.png" alt="SmartLog Logo" style={{ height: '80px', marginBottom: '16px' }} />
        <Typography variant="h2" component="h1" gutterBottom>
          Chào mừng đến với SmartLog Demand Forecast
        </Typography>
        <Typography variant="h5" color="text.secondary" sx={{ mb: 4 }}>
          Giải pháp thông minh để phân tích dữ liệu lịch sử và dự báo nhu cầu tương lai với độ chính xác cao.
        </Typography>
      </Box>

      <Paper elevation={3} sx={{ p: 4, mb: 6, bgcolor: 'background.default' }}>
        <Typography variant="h4" component="h2" gutterBottom sx={{ mb: 2, textAlign: 'center' }}>
          Về Dự án
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3, textAlign: 'justify' }}>
          Dự án SmartLog Demand Forecast là một công cụ mạnh mẽ được thiết kế để giúp các doanh nghiệp tối ưu hóa chuỗi cung ứng và quản lý hàng tồn kho. Bằng cách tận dụng các mô hình học máy tiên tiến, nền tảng của chúng tôi cung cấp các dự báo nhu cầu chính xác ở nhiều cấp độ khác nhau, từ các sản phẩm riêng lẻ (SKU) đến các kết hợp sản phẩm-khách hàng cụ thể.
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'justify' }}>
          Mục tiêu của chúng tôi là cung cấp cho bạn những thông tin chi tiết hữu ích, giảm thiểu sai sót trong dự báo và nâng cao hiệu quả hoạt động. Khám phá các chức năng bên dưới để bắt đầu.
        </Typography>
      </Paper>

      <Box sx={{ textAlign: 'center', mb: 6 }}>
        <Typography variant="h4" component="h2" gutterBottom>
          Các Chức Năng Chính
        </Typography>
      </Box>

      <Grid container spacing={4} justifyContent="center">
        {features.map((feature) => (
          <Grid item key={feature.title} xs={12} sm={6} md={4}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: 'background.paper', transition: 'transform 0.3s, box-shadow 0.3s', '&:hover': { transform: 'translateY(-5px)', boxShadow: theme.shadows[8] } }}>
              <CardActionArea onClick={() => navigate(feature.path)} sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 3 }}>
                <Box sx={{ mb: 2 }}>{feature.icon}</Box>
                <CardContent sx={{ textAlign: 'center', flexGrow: 1 }}>
                  <Typography gutterBottom variant="h5" component="div">
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {feature.description}
                  </Typography>
                </CardContent>
                <Box sx={{ mt: 'auto' }}>
                    <Button endIcon={<ArrowForwardIcon />}>
                        Truy cập
                    </Button>
                </Box>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};

export default Home;
