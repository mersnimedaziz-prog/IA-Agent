import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { BaseApiService } from './base-api.service';

@Injectable({
  providedIn: 'root'
})
export class MonthlyApiService extends BaseApiService {

  constructor(
    http: HttpClient,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    super(http, platformId);
  }

  uploadMonthlyFile(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<any>(`${this.apiUrl}/api/monthly/upload`, formData).pipe(
      tap(() => this.clearCache())
    );
  }

  getMonthlyResults(): Observable<any> {
    return this.getCached<any>(`${this.apiUrl}/api/monthly/results`);
  }

  getMonthlyTargets(): Observable<any> {
    return this.getCached<any>(`${this.apiUrl}/api/monthly/targets`);
  }

  saveMonthlyTarget(targetData: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/api/monthly/target`, targetData).pipe(
      tap(() => this.clearCache())
    );
  }

  calculateMonthlyKpi(calculationData: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/api/monthly/calculate`, calculationData).pipe(
      tap(() => this.clearCache())
    );
  }

  getMonthlyUploads() {
    return this.http.get<any>(`${this.apiUrl}/api/monthly/uploads`);
  }

  getMonthlyPivotByUpload(
    uploadId: string,
    month: string,
    startDate?: string,
    endDate?: string,
    analysisType: string = 'all'
  ) {
    let params = new HttpParams()
      .set('upload_id', uploadId)
      .set('month', month)
      .set('analysis_type', analysisType);

    if (startDate) params = params.set('start_date', startDate);
    if (endDate) params = params.set('end_date', endDate);

    return this.http.get<any>(`${this.apiUrl}/api/monthly/pivot-by-upload`, { params });
  }

  getMonthlyComparison(month: string, kpiName: string = 'monthly_total_hours'): Observable<any> {
    return this.getCached<any>(
      `${this.apiUrl}/api/monthly/comparison?month=${month}&kpi_name=${kpiName}`
    );
  }

  downloadMonthlyReport(uploadId: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/api/monthly/download-report/${uploadId}`, {
      responseType: 'blob'
    });
  }
}
