import { Component, OnInit, Inject, PLATFORM_ID, ChangeDetectorRef, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { Chart, registerables } from 'chart.js';
import { MonthlyApiService } from '../../services/monthly-api.service';

Chart.register(...registerables);

@Component({
  selector: 'app-summary-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './summary-dashboard.component.html',
  styleUrl: './summary-dashboard.component.css'
})
export class SummaryDashboardComponent implements OnInit, AfterViewInit {
  @ViewChild('summaryCanvas') summaryCanvas!: ElementRef<HTMLCanvasElement>;
  summaryChart: Chart | null = null;
  isBrowser = false;

  selectedMonth = '2026-05';

  results: any[] = [];
  targets: any[] = [];

  kpiRows: any[] = [];

  constructor(
    private apiService: MonthlyApiService,
    @Inject(PLATFORM_ID) private platformId: Object,
    private cdr: ChangeDetectorRef
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
  }

  ngOnInit(): void {
    if (this.isBrowser) {
      this.loadData();
    }
  }

  ngAfterViewInit(): void {
    // Chart will be rendered when data is ready
  }

  loadData(): void {
    forkJoin({
      results: this.apiService.getMonthlyResults(),
      targets: this.apiService.getMonthlyTargets()
    }).subscribe({
      next: (data) => {
        this.results = Array.isArray(data.results) ? data.results : [];
        this.targets = Array.isArray(data.targets) ? data.targets : [];
        this.calculateDashboard();
      },
      error: (err) => {
        console.error('Error loading dashboard data', err);
      }
    });
  }

  onMonthChange(): void {
    this.calculateDashboard();
  }

  calculateDashboard(): void {
    if (!this.selectedMonth) return;

    const [yearStr, monthStr] = this.selectedMonth.split('-');
    const currentYear = parseInt(yearStr, 10);
    const currentMonth = parseInt(monthStr, 10);

    // Filter data for the current year up to current month (for cumulative)
    // and for the specific month
    
    const kpiCode = "101";
    const kpiGroup = "DELIVERY";
    const kpiCriteria = "Total Hours Jira";
    const kpiUnit = "Hours";

    const getResult = (year: number, month: number) => {
      const mStr = `${year}-${String(month).padStart(2, '0')}`;
      const res = this.results.find(r => r.month === mStr && r.kpi_name === 'monthly_total_hours');
      return res ? res.value : 0;
    };

    const getTarget = (year: number, month: number) => {
      const mStr = `${year}-${String(month).padStart(2, '0')}`;
      const tgt = this.targets.find(t => t.month === mStr && t.kpi_name === 'monthly_total_hours');
      return tgt ? tgt.target_value : 0;
    };

    // Monthly values
    const act = getResult(currentYear, currentMonth);
    const trgt = getTarget(currentYear, currentMonth);
    const py = getResult(currentYear - 1, currentMonth);

    // Cumulative values
    let cumAct = 0;
    let cumTrgt = 0;
    let cumPy = 0;
    for (let i = 1; i <= currentMonth; i++) {
      cumAct += getResult(currentYear, i);
      cumTrgt += getTarget(currentYear, i);
      cumPy += getResult(currentYear - 1, i);
    }

    const calcPercent = (val: number, ref: number) => {
      if (ref === 0) return null;
      return Math.round((val / ref) * 100);
    };

    this.kpiRows = [
      {
        code: kpiCode,
        group: kpiGroup,
        criteria: kpiCriteria,
        unit: kpiUnit,
        monthly: {
          py: py,
          target: trgt,
          actual: act,
          actPyPercent: calcPercent(act, py),
          actTrgtPercent: calcPercent(act, trgt)
        },
        cumulative: {
          py: cumPy,
          target: cumTrgt,
          actual: cumAct,
          actPyPercent: calcPercent(cumAct, cumPy),
          actTrgtPercent: calcPercent(cumAct, cumTrgt)
        }
      }
    ];

    setTimeout(() => {
      this.renderChart(currentYear);
      this.cdr.detectChanges();
    }, 0);
  }

  renderChart(year: number): void {
    if (!this.isBrowser || !this.summaryCanvas) return;

    if (this.summaryChart) {
      this.summaryChart.destroy();
    }

    const ctx = this.summaryCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    const monthlyAct = [];
    const monthlyTrgt = [];
    const monthlyPy = [];

    const cumAct = [];
    const cumTrgt = [];
    const cumPy = [];

    let currentCumAct = 0;
    let currentCumTrgt = 0;
    let currentCumPy = 0;

    for (let m = 1; m <= 12; m++) {
      const mStr = `${year}-${String(m).padStart(2, '0')}`;
      const pyStr = `${year - 1}-${String(m).padStart(2, '0')}`;

      const res = this.results.find(r => r.month === mStr && r.kpi_name === 'monthly_total_hours')?.value || 0;
      const trgt = this.targets.find(t => t.month === mStr && t.kpi_name === 'monthly_total_hours')?.target_value || 0;
      const pyRes = this.results.find(r => r.month === pyStr && r.kpi_name === 'monthly_total_hours')?.value || 0;

      monthlyAct.push(res);
      monthlyTrgt.push(trgt);
      monthlyPy.push(pyRes);

      currentCumAct += res;
      currentCumTrgt += trgt;
      currentCumPy += pyRes;

      cumAct.push(currentCumAct);
      cumTrgt.push(currentCumTrgt);
      cumPy.push(currentCumPy);
    }

    this.summaryChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            type: 'line',
            label: 'Actual cum',
            data: cumAct,
            borderColor: 'black',
            backgroundColor: 'black',
            borderWidth: 2,
            tension: 0,
            yAxisID: 'y1'
          },
          {
            type: 'line',
            label: 'Target cum',
            data: cumTrgt,
            borderColor: 'red',
            backgroundColor: 'red',
            borderWidth: 2,
            tension: 0,
            yAxisID: 'y1'
          },
          {
            type: 'bar',
            label: 'Target',
            data: monthlyTrgt,
            backgroundColor: '#4e749e', // dark blue
            yAxisID: 'y'
          },
          {
            type: 'bar',
            label: 'Actual',
            data: monthlyAct,
            backgroundColor: '#ffc107', // yellow
            yAxisID: 'y'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          }
        },
        scales: {
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            title: {
              display: true,
              text: 'Monthly'
            }
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            title: {
              display: true,
              text: 'Cumulative'
            },
            grid: {
              drawOnChartArea: false
            }
          }
        }
      }
    });
  }
}
