import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { BaseApiService } from './base-api.service';

@Injectable({
  providedIn: 'root'
})
export class DashboardApiService extends BaseApiService {

  constructor(
    http: HttpClient,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    super(http, platformId);
  }

  healthCheck(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/api/health`);
  }

  uploadFile(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<any>(`${this.apiUrl}/api/upload`, formData).pipe(
      tap(() => this.clearCache())
    );
  }

  getKpis(): Observable<any> {
    return this.getCached<any>(`${this.apiUrl}/api/kpis`);
  }

  getCharts(): Observable<any> {
    return this.getCached<any>(`${this.apiUrl}/api/charts`);
  }
}
