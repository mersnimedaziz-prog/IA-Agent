import {
  Component,
  OnInit,
  AfterViewInit,
  ViewChild,
  ElementRef,
  Inject,
  PLATFORM_ID,
  ChangeDetectorRef
} from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Chart, registerables } from 'chart.js';

import { MonthlyApiService } from '../../services/monthly-api.service';
import { PageHeaderComponent } from '../../shared/page-header/page-header.component';

Chart.register(...registerables);

@Component({
  selector: 'app-monthly-tracking',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    PageHeaderComponent
  ],
  templateUrl: './monthly-tracking.component.html',
  styleUrl: './monthly-tracking.component.css'
})
export class MonthlyTrackingComponent implements OnInit, AfterViewInit {
  @ViewChild('monthlyComparisonCanvas')
  monthlyComparisonCanvas!: ElementRef<HTMLCanvasElement>;

  isBrowser = false;

  monthlySelectedFile: File | null = null;
  monthlyMonth = '2026-05';
  monthlyStartDate = '2026-05-01';
  monthlyEndDate = '2026-05-31';

  monthlyKpiName = 'monthly_total_hours';
  monthlyTargetValue = 60;

  isMonthlyUploading = false;
  isMonthlyCalculating = false;

  monthlyUploadMessage = '';
  monthlyErrorMessage = '';
  showFilters = true;

  uploadAuditAlert: any = null;
  monthlyCalculationResult: any = null;
  fileValidationResult: any = null;

  // Targets and Comparison properties
  monthlyResults: any[] = [];
  monthlyTargets: any[] = [];
  monthlyComparisonRows: any[] = [];
  monthlyComparisonChart: Chart | null = null;

  isLoadingTargets = false;
  isRecalculatingTargets = false;

  targetsSuccessMessage = '';
  targetsErrorMessage = '';

  constructor(
    private apiService: MonthlyApiService,
    @Inject(PLATFORM_ID) private platformId: Object,
    private cdr: ChangeDetectorRef
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
  }

  ngOnInit(): void {
    this.updateMonthlyDateRangeFromMonth();
    if (this.isBrowser) {
      this.loadMonthlyTargetsPageData();
    }
  }

  ngAfterViewInit(): void {
    // Le graphique est rendu après chargement des données.
  }

  updateMonthlyDateRangeFromMonth(): void {
    if (!this.monthlyMonth) {
      return;
    }

    const [year, month] = this.monthlyMonth.split('-').map(Number);

    if (!year || !month) {
      return;
    }

    const firstDay = new Date(year, month - 1, 1);
    const lastDay = new Date(year, month, 0);

    this.monthlyStartDate = this.formatDateForInput(firstDay);
    this.monthlyEndDate = this.formatDateForInput(lastDay);
  }

  formatDateForInput(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');

    return `${year}-${month}-${day}`;
  }

  onMonthlyFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;

    if (!input.files || input.files.length === 0) {
      this.monthlySelectedFile = null;
      return;
    }

    const file = input.files[0];
    const extension = file.name.split('.').pop()?.toLowerCase();

    if (!extension || !['xlsx', 'xls'].includes(extension)) {
      this.monthlySelectedFile = null;
      this.monthlyErrorMessage = 'Format non supporté. Veuillez importer un fichier Excel .xlsx ou .xls.';
      this.monthlyUploadMessage = '';
      return;
    }

    this.monthlySelectedFile = file;
    this.monthlyErrorMessage = '';
    this.monthlyUploadMessage = `Fichier mensuel sélectionné : ${file.name}`;
  }

  uploadAndCalculateMonthlyKpi(): void {
    if (!this.monthlySelectedFile) {
      this.monthlyErrorMessage = 'Veuillez sélectionner un fichier Jira mensuel avant de calculer.';
      this.monthlyUploadMessage = '';
      return;
    }

    if (!this.monthlyMonth) {
      this.monthlyErrorMessage = 'Veuillez choisir un mois.';
      return;
    }

    if (!this.monthlyStartDate || !this.monthlyEndDate) {
      this.monthlyErrorMessage = 'Veuillez choisir une date début et une date fin.';
      return;
    }

    if (this.monthlyStartDate > this.monthlyEndDate) {
      this.monthlyErrorMessage = 'La date début ne peut pas être supérieure à la date fin.';
      return;
    }

    if (
      this.monthlyTargetValue === null ||
      this.monthlyTargetValue === undefined
    ) {
      this.monthlyErrorMessage = 'Veuillez saisir un objectif mensuel.';
      return;
    }

    this.isMonthlyUploading = true;
    this.isMonthlyCalculating = false;
    this.monthlyErrorMessage = '';
    this.monthlyUploadMessage = 'Import du fichier mensuel en cours...';
    this.monthlyCalculationResult = null;
    this.uploadAuditAlert = null;
    this.fileValidationResult = null;

    this.apiService.uploadMonthlyFile(this.monthlySelectedFile).subscribe({
      next: (uploadRes: any) => {
        if (uploadRes?.error) {
          this.fileValidationResult = uploadRes?.validation || null;
          this.monthlyErrorMessage = uploadRes.error;
          this.monthlyUploadMessage = '';
          this.isMonthlyUploading = false;
          this.cdr.detectChanges();
          return;
        }

        this.fileValidationResult = uploadRes?.validation || null;
        this.uploadAuditAlert = uploadRes?.audit || null;

        this.monthlyUploadMessage =
          uploadRes?.message || 'Fichier mensuel importé avec succès.';

        this.isMonthlyUploading = false;
        this.cdr.detectChanges();

        this.saveTargetAndCalculate();
      },

      error: (err: any) => {
        console.error('Erreur upload mensuel:', err);

        this.fileValidationResult = err?.error?.validation || null;

        this.monthlyErrorMessage =
          err?.error?.error ||
          err?.error?.message ||
          err?.message ||
          'Erreur lors de l\'import du fichier mensuel.';

        this.monthlyUploadMessage = '';
        this.isMonthlyUploading = false;
        this.cdr.detectChanges();
      },

      complete: () => {
        this.isMonthlyUploading = false;
        this.cdr.detectChanges();
      }
    });
  }

  saveTargetAndCalculate(): void {
    this.isMonthlyCalculating = true;

    const targetPayload = {
      month: this.monthlyMonth,
      kpi_name: this.monthlyKpiName,
      target_value: Number(this.monthlyTargetValue),
      unit: 'hours',
      comparison: '>=',
      start_date: this.monthlyStartDate,
      end_date: this.monthlyEndDate
    };

    this.apiService.saveMonthlyTarget(targetPayload).subscribe({
      next: (targetRes: any) => {
        if (targetRes?.error) {
          this.monthlyErrorMessage = targetRes.error;
          this.isMonthlyCalculating = false;
          this.cdr.detectChanges();
          return;
        }

        const calculatePayload = {
          month: this.monthlyMonth,
          kpi_name: this.monthlyKpiName,
          start_date: this.monthlyStartDate,
          end_date: this.monthlyEndDate
        };

        this.apiService.calculateMonthlyKpi(calculatePayload).subscribe({
          next: (calcRes: any) => {
            if (calcRes?.error) {
              this.monthlyErrorMessage = calcRes.error;
              this.isMonthlyCalculating = false;
              this.cdr.detectChanges();
              return;
            }

            this.monthlyCalculationResult = calcRes;
            this.monthlyErrorMessage = '';

            this.monthlyUploadMessage =
              `Target du mois ${this.monthlyMonth} mis à jour et KPI recalculé avec succès.`;
            
            this.cdr.detectChanges();

            // Refresh targets after calculation
            if (this.isBrowser) {
              this.loadMonthlyTargetsPageData();
            }
          },

          error: (err: any) => {
            console.error('Erreur calcul mensuel:', err);
            this.monthlyErrorMessage = 'Erreur lors du calcul mensuel.';
            this.isMonthlyCalculating = false;
            this.cdr.detectChanges();
          },

          complete: () => {
            this.isMonthlyCalculating = false;
            this.cdr.detectChanges();
          }
        });
      },

      error: (err: any) => {
        console.error('Erreur sauvegarde target:', err);
        this.monthlyErrorMessage = 'Erreur lors de la sauvegarde du target mensuel.';
        this.isMonthlyCalculating = false;
        this.cdr.detectChanges();
      }
    });
  }

  getComparisonStatusLabel(): string {
    if (!this.monthlyCalculationResult?.comparison) {
      return '-';
    }

    return this.monthlyCalculationResult.comparison.achieved
      ? '✅ Objectif atteint'
      : '❌ Objectif non atteint';
  }

  getComparisonStatusClass(): string {
    if (!this.monthlyCalculationResult?.comparison) {
      return '';
    }

    return this.monthlyCalculationResult.comparison.achieved
      ? 'badge-success'
      : 'badge-danger';
  }

  // --- TARGETS & HISTORY METHODS --- //

  loadMonthlyTargetsPageData(): void {
    this.isLoadingTargets = true;
    this.targetsErrorMessage = '';
    this.targetsSuccessMessage = '';

    this.apiService.getMonthlyResults().subscribe({
      next: (resultsRes: any) => {
        this.monthlyResults = Array.isArray(resultsRes) ? resultsRes : [];

        this.apiService.getMonthlyTargets().subscribe({
          next: (targetsRes: any) => {
            this.monthlyTargets = Array.isArray(targetsRes) ? targetsRes : [];

            this.buildMonthlyComparisonRows();

            this.isLoadingTargets = false;
            this.cdr.detectChanges();
          },

          error: (err: any) => {
            console.error('Erreur chargement monthly targets:', err);
            this.targetsErrorMessage = 'Erreur lors du chargement des targets mensuels.';
            this.isLoadingTargets = false;
            this.cdr.detectChanges();
          },

          complete: () => {
            this.isLoadingTargets = false;
            this.cdr.detectChanges();
          }
        });
      },

      error: (err: any) => {
        console.error('Erreur chargement monthly results:', err);
        this.targetsErrorMessage = 'Erreur lors du chargement des résultats mensuels.';
        this.isLoadingTargets = false;
        this.cdr.detectChanges();
      }
    });
  }

  buildMonthlyComparisonRows(): void {
  const rows: any[] = [];

  for (const result of this.monthlyResults) {
    const resultStart =
      result.period_start ||
      this.getFirstDayOfMonth(result.month);

    const resultEnd =
      result.period_end ||
      this.getLastDayOfMonth(result.month);

    let target = this.monthlyTargets.find((t: any) =>
      t.month === result.month &&
      t.kpi_name === result.kpi_name &&
      (t.start_date || this.getFirstDayOfMonth(t.month)) === resultStart &&
      (t.end_date || this.getLastDayOfMonth(t.month)) === resultEnd
    );

    /*
      Fallback :
      Si aucun target avec même période n'est trouvé,
      on prend le target du même mois + même KPI.
      Utile pour les anciens targets sauvegardés sans start_date/end_date.
    */
    if (!target) {
      target = this.monthlyTargets.find((t: any) =>
        t.month === result.month &&
        t.kpi_name === result.kpi_name
      );
    }

    const resultValue = Number(result.value || 0);

    const targetValue =
      target && target.target_value !== null && target.target_value !== undefined
        ? Number(target.target_value)
        : null;

    let gap: number | null = null;
    let achieved = false;
    let status = 'Target manquant';

    if (targetValue !== null) {
      gap = Number((resultValue - targetValue).toFixed(2));

      const comparison = target?.comparison || '>=';

      if (comparison === '>=') {
        achieved = resultValue >= targetValue;
      } else if (comparison === '<=') {
        achieved = resultValue <= targetValue;
      } else if (comparison === '=') {
        achieved = resultValue === targetValue;
      }

      status = achieved ? 'Atteint' : 'Non atteint';
    }

    rows.push({
      month: result.month,
      compilation_date: result.compilation_date,
      kpi_name: result.kpi_name,
      result_value: resultValue,
      target_value: targetValue,
      unit: result.unit || target?.unit || 'hours',
      comparison: target?.comparison || '>=',
      gap,
      achieved,
      status,
      period_start: resultStart,
      period_end: resultEnd
    });
  }

  this.monthlyComparisonRows = rows.sort((a: any, b: any) => {
    return new Date(a.compilation_date).getTime() - new Date(b.compilation_date).getTime();
  });

  setTimeout(() => {
    this.renderMonthlyComparisonChart();
  }, 150);
  }

  getMonthlyResultRows(): any[] {
    return [...this.monthlyResults].sort((a: any, b: any) => {
      return new Date(a.compilation_date).getTime() - new Date(b.compilation_date).getTime();
    });
  }

  getMonthlyTargetRows(): any[] {
    return [...this.monthlyTargets].sort((a: any, b: any) => {
      return new Date(a.compilation_date).getTime() - new Date(b.compilation_date).getTime();
    });
  }

  formatCompilationDate(dateValue: string): string {
    if (!dateValue) {
      return '-';
    }

    const date = new Date(dateValue);

    return date.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  }

  getResultValue(row: any): number | string {
    if (!row) {
      return '-';
    }

    if (row.value !== null && row.value !== undefined) {
      return row.value;
    }

    return '-';
  }

  getTargetValue(row: any): number | string {
    if (!row) {
      return '-';
    }

    if (row.target_value !== null && row.target_value !== undefined) {
      return row.target_value;
    }

    return '-';
  }

  refreshTargetAndRecalculate(row: any): void {
  if (!row) {
    this.targetsErrorMessage = 'Aucun target sélectionné.';
    return;
  }

  if (!row.month) {
    this.targetsErrorMessage = 'Mois introuvable pour ce target.';
    return;
  }

  if (
    row.target_value === null ||
    row.target_value === undefined ||
    row.target_value === ''
  ) {
    this.targetsErrorMessage = 'Veuillez saisir une valeur target valide.';
    return;
  }

  this.isRecalculatingTargets = true;
  this.targetsErrorMessage = '';
  this.targetsSuccessMessage = '';

  const startDate =
    row.start_date ||
    row.period_start ||
    this.getFirstDayOfMonth(row.month);

  const endDate =
    row.end_date ||
    row.period_end ||
    this.getLastDayOfMonth(row.month);

  const targetPayload = {
    month: row.month,
    kpi_name: row.kpi_name || 'monthly_total_hours',
    target_value: Number(row.target_value),
    unit: row.unit || 'hours',
    comparison: row.comparison || '>=',
    start_date: startDate,
    end_date: endDate
  };

  this.apiService.saveMonthlyTarget(targetPayload).subscribe({
    next: (targetRes: any) => {
      if (targetRes?.error) {
        this.targetsErrorMessage = targetRes.error;
        this.isRecalculatingTargets = false;
        this.cdr.detectChanges();
        return;
      }

      this.targetsSuccessMessage =
        `Target du mois ${row.month} mis à jour avec succès.`;

      /*
        Important :
        On recharge seulement l'historique.
        On ne recalcule PAS le résultat ici.
        Le résultat doit rester celui déjà calculé depuis le fichier Jira importé.
      */
      this.loadMonthlyTargetsPageData();

      this.isRecalculatingTargets = false;
      this.cdr.detectChanges();
    },

    error: (err: any) => {
      console.error('Erreur sauvegarde target modifié:', err);
      this.targetsErrorMessage = 'Erreur lors de la mise à jour du target.';
      this.isRecalculatingTargets = false;
      this.cdr.detectChanges();
    },

    complete: () => {
      this.isRecalculatingTargets = false;
      this.cdr.detectChanges();
    }
  });
  }

  refreshAllData(): void {
    this.loadMonthlyTargetsPageData();
  }

  renderMonthlyComparisonChart(): void {
    if (!this.isBrowser) {
      return;
    }

    if (!this.monthlyComparisonCanvas) {
      console.warn('Canvas monthlyComparisonCanvas non disponible.');
      return;
    }

    if (!this.monthlyComparisonRows || this.monthlyComparisonRows.length === 0) {
      console.warn('Aucune donnée pour le graphique monthly comparison.');
      return;
    }

    if (this.monthlyComparisonChart) {
      this.monthlyComparisonChart.destroy();
    }

    const ctx = this.monthlyComparisonCanvas.nativeElement.getContext('2d');

    if (!ctx) {
      console.warn('Contexte canvas introuvable.');
      return;
    }

    const labels = this.monthlyComparisonRows.map((row: any) => row.month);
    const resultData = this.monthlyComparisonRows.map((row: any) => row.result_value);
    const targetData = this.monthlyComparisonRows.map((row: any) => row.target_value || 0);

    this.monthlyComparisonChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Result',
            data: resultData,
            backgroundColor: '#3b82f6',
            borderColor: '#1d4ed8',
            borderWidth: 1,
            borderRadius: 8
          },
          {
            label: 'Target',
            data: targetData,
            backgroundColor: '#f97316',
            borderColor: '#c2410c',
            borderWidth: 1,
            borderRadius: 8
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true
          },
          title: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              precision: 0
            }
          }
        }
      }
    });
  }

  getFirstDayOfMonth(month: string): string {
    if (!month) {
      return '';
    }

    return `${month}-01`;
  }

  downloadReport(): void {
    if (!this.monthlyCalculationResult?.upload?.upload_id) {
      this.monthlyErrorMessage = 'Aucun fichier calculé disponible pour le téléchargement.';
      return;
    }
    
    const uploadId = this.monthlyCalculationResult.upload.upload_id;
    
    this.apiService.downloadMonthlyReport(uploadId).subscribe({
      next: (blob: Blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        const filename = `Rapport_Analyse_${this.monthlyCalculationResult.upload.original_filename || 'Jira'}.xlsx`;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        
        window.URL.revokeObjectURL(url);
        a.remove();
      },
      error: (err) => {
        console.error('Erreur lors du téléchargement du rapport:', err);
        this.monthlyErrorMessage = 'Erreur lors du téléchargement du rapport Excel.';
        this.cdr.detectChanges();
      }
    });
  }

  getLastDayOfMonth(month: string): string {
    if (!month) {
      return '';
    }

    const [year, monthNumber] = month.split('-').map(Number);

    if (!year || !monthNumber) {
      return '';
    }

    const lastDay = new Date(year, monthNumber, 0);
    const y = lastDay.getFullYear();
    const m = String(lastDay.getMonth() + 1).padStart(2, '0');
    const d = String(lastDay.getDate()).padStart(2, '0');

    return `${y}-${m}-${d}`;
  }
}