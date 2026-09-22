import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

import {
  CertificateService,
  Certificate
} from '../../../core/services/certificate';

@Component({
  selector: 'app-certificate-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './certificate-list.html',
  styleUrl: './certificate-list.scss'
})
export class CertificateListComponent implements OnInit {
  private readonly certificateService = inject(CertificateService);
  private readonly router = inject(Router);

  certificates: Certificate[] = [];
  loading = true;
  errorMessage = '';

  ngOnInit(): void {
    this.loadCertificates();
  }

  loadCertificates(): void {
    this.loading = true;
    this.errorMessage = '';

    this.certificateService.getCertificates().subscribe({
      next: certificates => {
        this.certificates = certificates;
        this.loading = false;
      },

      error: error => {
        console.error('Failed to load certificates:', error);

        this.loading = false;

        if (error.status === 401) {
          this.errorMessage =
            'Your session has expired. Please log in again.';
        } else if (error.status === 403) {
          this.errorMessage =
            'You are not allowed to view these certificates.';
        } else {
          this.errorMessage =
            'Unable to load your certificates. Please try again.';
        }
      }
    });
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  }

  viewCertificate(id: number): void {
    this.router.navigate([
      '/certificates',
      id
    ]);
  }

  verifyCertificate(certificateId: string): void {
    const verificationUrl =
      `${window.location.origin}/certificates/verify/${certificateId}`;

    window.open(
      verificationUrl,
      '_blank',
      'noopener,noreferrer'
    );
  }

  goToCourses(): void {
    this.router.navigate([
      '/courses'
    ]);
  }
}