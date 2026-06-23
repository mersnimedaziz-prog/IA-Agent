import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PageHeaderComponent } from '../../shared/page-header/page-header.component';
import { SummaryDashboardComponent } from '../summary-dashboard/summary-dashboard.component';

@Component({
  selector: 'app-home',
  imports: [RouterLink, PageHeaderComponent, SummaryDashboardComponent],
  templateUrl: './home.component.html'
})
export class HomeComponent {}
