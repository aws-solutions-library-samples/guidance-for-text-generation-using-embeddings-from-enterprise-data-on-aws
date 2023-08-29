import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useAuthenticator, View  } from '@aws-amplify/ui-react';

import logo from './logo.svg';
import './App.css';

import ResponsiveAppBar from './ResponsiveAppBar' ;
import { Login } from './Login' ;
import  GenerateText from './TestTextGen' ;
import GenerateImage from './GenImage' ;
import ArchView from './Arch' ;
import LegalLLMRAG from './LegalLLMRAG';

function App() {
  const { user, signOut } = useAuthenticator((context) => [context.user]);

  return (
    <>
      <ResponsiveAppBar/>      
      <Router>
        <View padding="1rem">
          <Suspense fallback={'loading...'}>
            <Routes>
              <Route path="/" />
              <Route path="/login" element={<Login />} />
              <Route path="/TextGenerate" element={ <GenerateText /> } />
              <Route path="/arch" element={ <ArchView/> } />
              <Route path="/ImageGenerate" element={ <GenerateImage /> } />
              <Route path="/LegalLLMRAG" element={ <LegalLLMRAG /> } />
            </Routes>
          </Suspense>
        </View>
      </Router>
    </>
  );
}

export default App;
