import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
// 1. On importe notre VRAI composant
import { AppComponent } from './app/app.component'; 

// 2. On dit à Angular de démarrer sur AppComponent
bootstrapApplication(AppComponent, appConfig)
  .catch((err) => console.error(err));