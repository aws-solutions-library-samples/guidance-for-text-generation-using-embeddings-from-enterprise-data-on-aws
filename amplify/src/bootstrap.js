import React from 'react';
import ReactDOM from 'react-dom/client';

import "@aws-amplify/ui-react/styles.css";
import '@fontsource/roboto/300.css';
import '@fontsource/roboto/400.css';
import '@fontsource/roboto/500.css';
import '@fontsource/roboto/700.css';

import { ThemeProvider } from "@aws-amplify/ui-react";
import { Amplify } from 'aws-amplify';

import { Authenticator } from '@aws-amplify/ui-react';

import studioTheme from './ui-components/studioTheme';
import App from './App';

import reportWebVitals from './reportWebVitals';

import cnf from './cdk-exports.json';

Amplify.configure({
  Auth: {
    identityPoolId : cnf.GenAIAmplifyAppAPILambdaStack.CognitoIdentityPoolId,
    region: cnf.GenAIAmplifyAppAPILambdaStack.appregion,
    userPoolId: cnf.GenAIAmplifyAppAPILambdaStack.CognitoUserPoolId,
    userPoolWebClientId: cnf.GenAIAmplifyAppAPILambdaStack.GenAIReactAmplifyClientId
  },
  API: {
    endpoints: [
      {
        name: cnf.GenAIAmplifyAppAPILambdaStack.llmragapiname,
        endpoint: cnf.GenAIAmplifyAppAPILambdaStack.llmragapiendpoint
      },
      {
        name: cnf.GenAIAmplifyAppAPILambdaStack.txt2imgapiname,
        endpoint: cnf.GenAIAmplifyAppAPILambdaStack.txt2imgapiendpoint
      },
      {
        name: cnf.GenAIAmplifyAppAPILambdaStack.txt2txtapiname,
        endpoint: cnf.GenAIAmplifyAppAPILambdaStack.txt2txtapiendpoint
      }        
    ]
  }
});

const root = ReactDOM.createRoot(
  document.getElementById('root')
);

root.render(
  <React.StrictMode>
      <ThemeProvider theme={studioTheme}>
        <Authenticator.Provider>
          <App />
        </Authenticator.Provider>
      </ThemeProvider>
  </React.StrictMode>
);

export {} ;
reportWebVitals();