import * as React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';

import { useAuthenticator, View } from '@aws-amplify/ui-react';

const menuItems = [ 
  {
    menuTitle: "Home",
    pageUrl: "/"
  },
  {
    menuTitle: "Generate Text",
    pageUrl: "/TextGenerate"
  },
  {
    menuTitle: "Generate Image",
    pageUrl: "/ImageGenerate"
  },
  {
    menuTitle: "Legal Docs Q&A",
    pageUrl: "/LegalLLMRAG"
  },    
  {
    menuTitle: "Arch",
    pageUrl: "/arch"
  },
];

function ResponsiveAppBar() {
  const [anchorEl, setAnchorEl] = React.useState(null);

  const { user, signOut } = useAuthenticator((context) => [context.user]);

  const { authStatus } = useAuthenticator(context => [context.authStatus]);

  function logOut() {
    signOut();
  }

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  }; 
 
  const handleClose = () => {
    setAnchorEl(null);
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Generative AI Demo
            </Typography>

            { authStatus === 'authenticated' ? (
              <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' } }}>
                  { menuItems.map((menuItem) => (
                    <Button key={ menuItem.menuTitle } href={ menuItem.pageUrl } color="inherit" sx={{ my: 2, color: 'white', display: 'block' }}>
                      { menuItem.menuTitle }
                    </Button>
                  ))}
              </Box>
              ) : (
                <div></div>
            )}
            
            { 
              authStatus !== 'authenticated' ? (
                <>
                  <Button color="inherit" href= {'/login'}>Login</Button>
                </>
              ) : (
                <Button onClick={() => logOut()}>Logout</Button>
              )
            }
          </Toolbar>
      </AppBar>
    </Box>
  );
}
export default ResponsiveAppBar;

