import { Component, OnInit, Inject, PLATFORM_ID, ChangeDetectorRef, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize, take, timeout, catchError } from 'rxjs';
import { of } from 'rxjs';

import { MonthlyApiService } from '../../services/monthly-api.service';
import { PageHeaderComponent } from '../../shared/page-header/page-header.component';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-daily-summary',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    PageHeaderComponent
  ],
  templateUrl: './daily-summary.component.html',
  styleUrl: './daily-summary.component.css'
})
export class DailySummaryComponent implements OnInit, AfterViewInit {
  @ViewChild('throughputCanvas') throughputCanvas!: ElementRef<HTMLCanvasElement>;
  throughputChart: Chart | null = null;

  isBrowser = false;

  month = '2026-05';
  startDate = '2026-05-01';
  endDate = '2026-05-31';

  isLoading = false;

  errorMessage = '';
  successMessage = '';
  showFilters = true;

  dailySummary: any[] = [];

  totalHours = 0;
  totalMd = 0;
  totalDays = 0;

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

  ngAfterViewInit(): void {
    if (this.isBrowser && this.dailySummary.length > 0) {
      this.renderThroughputChart();
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

  loadDailySummary(): void {
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
    this.errorMessage = '';
    this.successMessage = '';

    this.dailySummary = [];
    this.resetTotals();

    this.apiService
      .getMonthlyPivotByUpload(
        this.selectedUploadId,
        this.month,
        this.startDate,
        this.endDate,
        'daily'
      )
      .pipe(
        timeout(15000),
        take(1),
        catchError((err: any) => {
          console.error('Erreur ou timeout chargement résumé journalier:', err);
          this.errorMessage = err?.name === 'TimeoutError'
            ? 'Le serveur met trop de temps à répondre. Veuillez réessayer.'
            : 'Erreur lors du chargement du résumé par journée.';
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
          this.dailySummary = res?.daily_summary || [];
          this.calculateTotals();
          
          if (this.isBrowser) {
            setTimeout(() => {
              this.renderThroughputChart();
            }, 0);
          }

          this.successMessage = `Résumé journalier chargé pour la période ${this.startDate} → ${this.endDate}.`;
          this.cdr.detectChanges();
        },
        error: (err: any) => {
          console.error('Erreur chargement résumé journalier:', err);
          this.errorMessage = 'Erreur lors du chargement du résumé par journée.';
          this.cdr.detectChanges();
        }
      });
  }

  calculateTotals(): void {
    this.totalHours = this.dailySummary.reduce((sum: number, row: any) => {
      return sum + Number(row.Total_Hours || 0);
    }, 0);

    this.totalHours = Number(this.totalHours.toFixed(2));
    this.totalMd = Number((this.totalHours / 8).toFixed(2));
    this.totalDays = this.dailySummary.length;
  }

  resetTotals(): void {
    this.totalHours = 0;
    this.totalMd = 0;
    this.totalDays = 0;
  }

  getActivityList(row: any): string[] {
    if (Array.isArray(row?.Activities)) {
      return row.Activities;
    }

    if (row?.Activities_Text) {
      return String(row.Activities_Text)
        .split('|')
        .map((item: string) => item.trim())
        .filter((item: string) => item.length > 0);
    }

    return [];
  }

  getDayStatus(row: any): string {
    const hours = Number(row?.Total_Hours || 0);

    if (hours === 0) {
      return 'Repos / Holiday';
    }

    if (hours < 6) {
      return 'Charge faible';
    }

    if (hours <= 9) {
      return 'Charge normale';
    }

    return 'Charge élevée';
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
          this.selectedUploadInfo = res?.upload || this.selectedUploadInfo;

          if (this.monthlyUploads.length > 0) {
            if (!this.selectedUploadId) {
              this.selectedUploadId = this.monthlyUploads[0].upload_id;
              this.selectedUploadInfo = this.monthlyUploads[0];
            }
            this.loadDailySummary();
          }
          this.cdr.detectChanges();
        }
      });
  }

  getDayStatusClass(row: any): string {
    const hours = Number(row?.Total_Hours || 0);

    if (hours === 0) {
      return 'badge-secondary';
    }

    if (hours < 6) {
      return 'badge-warning';
    }

    if (hours <= 9) {
      return 'badge-success';
    }

    return 'badge-danger';
  }

  renderThroughputChart(): void {
    if (!this.isBrowser) {
      return;
    }

    if (!this.throughputCanvas) {
      console.warn('Canvas throughputCanvas non disponible.');
      return;
    }

    if (!this.dailySummary || this.dailySummary.length === 0) {
      return;
    }

    if (this.throughputChart) {
      this.throughputChart.destroy();
    }

    const ctx = this.throughputCanvas.nativeElement.getContext('2d');

    if (!ctx) {
      return;
    }

    const sortedData = [...this.dailySummary].sort((a, b) => {
      const dateA = new Date(a.Date).getTime();
      const dateB = new Date(b.Date).getTime();
      return dateA - dateB;
    });

    const labels = sortedData.map(row => row.Date);
    const hoursData = sortedData.map(row => Number(row.Total_Hours || 0));

    this.throughputChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Throughput (Heures totales)',
            data: hoursData,
            backgroundColor: 'rgba(59, 130, 246, 0.2)',
            borderColor: '#3b82f6',
            borderWidth: 2,
            pointBackgroundColor: '#1d4ed8',
            pointRadius: 4,
            fill: true,
            tension: 0.3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          title: {
            display: true,
            text: 'Évolution du Throughput Quotidien (Heures)',
            padding: {
              bottom: 20
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Heures'
            }
          },
          x: {
            title: {
              display: true,
              text: 'Date'
            }
          }
        }
      }
    });
  }
}