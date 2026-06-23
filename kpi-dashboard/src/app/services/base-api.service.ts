import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Observable, shareReplay } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class BaseApiService {
  protected apiUrl = 'http://localhost:8082';
  private cache = new Map<string, Observable<any>>();

  constructor(
    protected http: HttpClient,
    @Inject(PLATFORM_ID) protected platformId: Object
  ) {
    if (!isPlatformBrowser(this.platformId)) {
      // In SSR (Docker container), use the internal Docker network hostname
      this.apiUrl = process.env['API_URL'] || 'http://backend:8000';
    } else {
      // In browser, use the exposed localhost port
      this.apiUrl = 'http://localhost:8082';
    }
  }

  protected getCached<T>(url: string): Observable<T> {
    if (!this.cache.has(url)) {
      const request$ = this.http.get<T>(url).pipe(
        shareReplay(1)
      );
      this.cache.set(url, request$);
    }
    return this.cache.get(url) as Observable<T>;
  }

  clearCache(): void {
    this.cache.clear();
  }
}
