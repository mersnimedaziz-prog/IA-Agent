import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BaseApiService } from './base-api.service';

@Injectable({
  providedIn: 'root'
})
export class TimesheetsApiService extends BaseApiService {

  constructor(
    http: HttpClient,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    super(http, platformId);
  }

  getTimesheetValidation(): Observable<any> {
    return this.getCached<any>(`${this.apiUrl}/api/timesheets/validation`);
  }

  getTimesheetValidations(): Observable<any> {
    return this.getTimesheetValidation();
  }

  getOllamaStatus(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/api/ollama/status`);
  }

  explainTimesheet(row: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/api/timesheets/explain`, row);
  }

  getAiKpiSummary(): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/api/kpis/summary`, {});
  }
}
