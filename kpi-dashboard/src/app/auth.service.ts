import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import Keycloak from 'keycloak-js';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private keycloak: Keycloak | null = null;
  private isBrowser: boolean;

  constructor(@Inject(PLATFORM_ID) private platformId: Object) {
    this.isBrowser = isPlatformBrowser(this.platformId);

    if (this.isBrowser) {
      this.keycloak = new Keycloak({
        url: 'http://localhost:8081',
        realm: 'ia-agent',
        clientId: 'angular-client'
      });
    }
  }

  async init(): Promise<boolean> {
    if (!this.isBrowser || !this.keycloak) {
      return false;
    }

    try {
      const authenticated = await this.keycloak.init({
        onLoad: 'check-sso',
        checkLoginIframe: false,
        pkceMethod: 'S256'
      });

      return authenticated;
    } catch (error) {
      console.error('Erreur initialisation Keycloak:', error);
      return false;
    }
  }

  login(): void {
    if (!this.isBrowser || !this.keycloak) {
      return;
    }

    this.keycloak.login({
      redirectUri: window.location.origin,
      prompt: 'login'
    });
  }

  logout(): void {
    if (!this.isBrowser || !this.keycloak) {
      return;
    }

    this.keycloak.logout({
      redirectUri: window.location.origin
    });
  }

  isLoggedIn(): boolean {
    if (!this.isBrowser || !this.keycloak) {
      return false;
    }

    return !!this.keycloak.authenticated;
  }

  getUsername(): string {
    if (!this.isBrowser || !this.keycloak) {
      return '';
    }

    const tokenParsed: any = this.keycloak.tokenParsed;

    return (
      tokenParsed?.preferred_username ||
      tokenParsed?.name ||
      tokenParsed?.email ||
      'Utilisateur'
    );
  }

  getFullName(): string {
    if (!this.isBrowser || !this.keycloak) {
      return '';
    }

    const tokenParsed: any = this.keycloak.tokenParsed;

    return (
      tokenParsed?.name ||
      tokenParsed?.preferred_username ||
      'Utilisateur connecté'
    );
  }

  getToken(): string | undefined {
    if (!this.isBrowser || !this.keycloak) {
      return undefined;
    }

    return this.keycloak.token;
  }

  getRoles(): string[] {
    if (!this.isBrowser || !this.keycloak) {
      return [];
    }

    const tokenParsed: any = this.keycloak.tokenParsed;

    return tokenParsed?.realm_access?.roles || [];
  }
}
