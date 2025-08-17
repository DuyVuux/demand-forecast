import React, { useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Box, AppBar, Toolbar, Drawer, List, ListItemButton, ListItemIcon,
  ListItemText, Typography, IconButton, Select, MenuItem, Tooltip, useTheme, useMediaQuery
} from '@mui/material';
import {
  Menu as MenuIcon,
  Home as HomeIcon,
  Analytics as AnalyticsIcon,
  Factory as FactoryIcon,
  Inventory2 as SkuIcon,
  Language as LanguageIcon,
  ChevronLeft as ChevronLeftIcon
} from '@mui/icons-material';

const drawerWidth = 240;

const navItems = [
  { text: 'Data Analysis', path: '/data-analysis', icon: <AnalyticsIcon /> },
  { text: 'PC Forecast', path: '/pc-forecast', icon: <FactoryIcon /> },
  { text: 'SKU Forecast', path: '/sku-forecast', icon: <SkuIcon /> },
];

const MainLayout = () => {
  const [language, setLanguage] = useState('EN');
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleLanguageChange = (event) => {
    setLanguage(event.target.value);
    // In a real app, you would trigger the language change here
  };

  const drawerContent = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Toolbar sx={{ justifyContent: 'center', py: 2, flexShrink: 0 }}>
        <Typography variant="h5" noWrap component="div" fontWeight="bold">
          DemandTTC
        </Typography>
      </Toolbar>
      <List sx={{ overflowY: 'auto' }}>
        {navItems.map((item) => (
          <ListItemButton
            key={item.text}
            onClick={() => { navigate(item.path); if (isMobile) handleDrawerToggle(); }}
            selected={location.pathname === item.path}
            sx={{
              margin: '4px 8px',
              borderRadius: '8px',
              '&.Mui-selected': {
                backgroundColor: theme.palette.primary.main,
                color: theme.palette.primary.contrastText,
                '&:hover': {
                  backgroundColor: theme.palette.primary.dark,
                },
                '.MuiListItemIcon-root': {
                  color: theme.palette.primary.contrastText,
                }
              },
            }}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          backgroundColor: 'background.paper',
          backgroundImage: 'none',
          borderBottom: '1px solid', 
          borderColor: 'divider'
        }}
      >
        <Toolbar>
          {isMobile && (
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Tooltip title="Go to Home">
            <IconButton color="inherit" onClick={() => navigate('/')}>
              <HomeIcon />
            </IconButton>
          </Tooltip>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, ml: 1 }}>
            {navItems.find(item => item.path === location.pathname)?.text || 'Home'}
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <LanguageIcon sx={{ mr: 1, color: 'text.secondary' }} />
            <Select
              value={language}
              onChange={handleLanguageChange}
              variant="standard"
              disableUnderline
              sx={{
                color: 'text.primary',
                '.MuiSelect-icon': {
                  color: 'text.secondary',
                },
              }}
            >
              <MenuItem value="EN">EN</MenuItem>
              <MenuItem value="VN">VN</MenuItem>
            </Select>
          </Box>
        </Toolbar>
      </AppBar>
      
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant={isMobile ? 'temporary' : 'permanent'}
          open={isMobile ? mobileOpen : true}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth, 
              backgroundColor: 'background.default',
              borderRight: 'none'
            },
          }}
        >
          {drawerContent}
        </Drawer>
      </Box>

      <Box component="main" sx={{ flexGrow: 1, p: 3, width: { sm: `calc(100% - ${drawerWidth}px)` } }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
};

export default MainLayout;
