import { Component, OnInit, Inject, PLATFORM_ID, ChangeDetectorRef } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize, take, timeout, catchError } from 'rxjs';
import { of } from 'rxjs';

import { MonthlyApiService } from '../../services/monthly-api.service';
import { PageHeaderComponent } from '../../shared/page-header/page-header.component';

@Component({
  selector: 'app-role-summary',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    PageHeaderComponent
  ],
  templateUrl: './role-summary.component.html',
  styleUrl: './role-summary.component.css'
})
export class RoleSummaryComponent implements OnInit {
  isBrowser = false;

  month = '2026-05';
  startDate = '2026-05-01';
  endDate = '2026-05-31';

  isLoading = false;

  successMessage = '';
  errorMessage = '';
  showFilters = true;

  byRole: any[] = [];
  roleWorkSummary: any[] = [];

  totalHours = 0;
  totalMd = 0;
  totalRoles = 0;
  totalTickets = 0;

  monthlyUploads: any[] = [];
  selectedUploadId = '';
  selectedUploadInfo: any = null;


  constructor(
    private apiService: MonthlyApiService,
    @Inject(PLATFORM_ID) private platformId: Object,
    private cdr: ChangeDetectorRef
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
  }

  ngOnInit(): void {
    this.updateDateRangeFromMonth();
    if (this.isBrowser) {
      this.loadMonthlyUploads();
    }
  }

  updateDateRangeFromMonth(): void {
    if (!this.month) {
      return;
    }

    const [year, monthNumber] = this.month.split('-').map(Number);

    if (!year || !monthNumber) {
      return;
    }

    const firstDay = new Date(year, monthNumber - 1, 1);
    const lastDay = new Date(year, monthNumber, 0);

    this.startDate = this.formatDateForInput(firstDay);
    this.endDate = this.formatDateForInput(lastDay);
  }

  formatDateForInput(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');

    return `${year}-${month}-${day}`;
  }

  loadMonthlyUploads(): void {
    this.apiService.getMonthlyUploads()
      .pipe(
        timeout(10000),
        take(1),
        catchError((err: any) => {
          console.error('Erreur ou timeout chargement historique fichiers:', err);
          this.cdr.detectChanges();
          return of([]);
        })
      )
      .subscribe({
        next: (res: any) => {
          this.monthlyUploads = Array.isArray(res) ? res : [];

          if (this.monthlyUploads.length > 0) {
            if (!this.selectedUploadId) {
              this.selectedUploadId = this.monthlyUploads[0].upload_id;
              this.selectedUploadInfo = this.monthlyUploads[0];
            }
            this.loadRoleSummary();
          }
          this.cdr.detectChanges();
        }
      });
  }

  loadRoleSummary(): void {
    if (!this.month) {
      this.errorMessage = 'Veuillez sélectionner un mois.';
      return;
    }

    if (!this.startDate || !this.endDate) {
      this.errorMessage = 'Veuillez sélectionner une date début et une date fin.';
      return;
    }

    if (this.startDate > this.endDate) {
      this.errorMessage = 'La date début ne peut pas être supérieure à la date fin.';
      return;
    }

    if (!this.selectedUploadId) {
      this.errorMessage = 'Veuillez sélectionner un fichier source.';
      return;
    }

    this.isLoading = true;
    this.successMessage = '';
    this.errorMessage = '';

    this.byRole = [];
    this.roleWorkSummary = [];
    this.resetTotals();

    this.apiService
      .getMonthlyPivotByUpload(
        this.selectedUploadId,
        this.month,
        this.startDate,
        this.endDate,
        'role'
      )
      .pipe(
        timeout(15000),
        take(1),
        catchError((err: any) => {
          console.error('Erreur ou timeout chargement résumé par rôle:', err);
          this.errorMessage = err?.name === 'TimeoutError'
            ? 'Le serveur met trop de temps à répondre. Veuillez réessayer.'
            : 'Erreur lors du chargement du résumé par rôle.';
          this.isLoading = false;
          this.cdr.detectChanges();
          return of(null);
        }),
        finalize(() => {
          this.isLoading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: (res: any) => {
          if (!res) return;

          if (res?.error) {
            this.errorMessage = res.error;
            this.cdr.detectChanges();
            return;
          }

          this.selectedUploadInfo = res?.upload || this.selectedUploadInfo;

          this.byRole = Array.isArray(res?.by_role) ? res.by_role : [];
          this.roleWorkSummary = Array.isArray(res?.role_work_summary)
            ? res.role_work_summary
            : [];

          this.calculateTotals();

          this.successMessage = `Résumé par rôle chargé pour la période ${this.startDate} → ${this.endDate}.`;
          this.cdr.detectChanges();
        },

        error: (err: any) => {
          console.error('Erreur chargement résumé par rôle:', err);
          this.errorMessage = 'Erreur lors du chargement du résumé par rôle.';
          this.cdr.detectChanges();
        }
      });
  }

  calculateTotals(): void {
    this.totalHours = this.byRole.reduce((sum: number, row: any) => {
      return sum + Number(row.Time_Hours || row.Total_Hours || 0);
    }, 0);

    this.totalHours = Number(this.totalHours.toFixed(2));
    this.totalMd = Number((this.totalHours / 8).toFixed(2));
    this.totalRoles = this.byRole.length;

    this.totalTickets = this.roleWorkSummary.reduce((sum: number, row: any) => {
      return sum + Number(row.Tickets_Count || 0);
    }, 0);
  }

  resetTotals(): void {
    this.totalHours = 0;
    this.totalMd = 0;
    this.totalRoles = 0;
    this.totalTickets = 0;
  }

  getRoleHours(row: any): number {
    return Number(row.Time_Hours || row.Total_Hours || 0);
  }

  getRoleMd(row: any): number {
    if (row.Total_MD !== null && row.Total_MD !== undefined) {
      return Number(row.Total_MD);
    }

    return Number((this.getRoleHours(row) / 8).toFixed(2));
  }

  getWorkItems(row: any): string[] {
    if (Array.isArray(row?.Worked_On)) {
      return row.Worked_On;
    }

    if (row?.Worked_On_Text) {
      return String(row.Worked_On_Text)
        .split('|')
        .map((item: string) => item.trim())
        .filter((item: string) => item.length > 0);
    }

    return [];
  }

  getRoleBadgeClass(role: string): string {
    const normalized = String(role || '').toUpperCase();

    if (normalized.includes('FE')) {
      return 'bg-info';
    }

    if (normalized.includes('BE')) {
      return 'bg-primary';
    }

    if (normalized.includes('QA')) {
      return 'bg-success';
    }

    return 'bg-secondary';
  }

  getWorkSummaryForRole(role: string): any | null {
    return this.roleWorkSummary.find((row: any) => row.Role === role) || null;
  }
}