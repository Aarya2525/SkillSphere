import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Certificate {
  id: number;
  certificate_id: string;
  student: number;
  student_name: string;
  course: number;
  course_title: string;
  issued_at: string;
  completion_percentage: number;
}

export interface CertificateCreateRequest {
  course: number;
}

export interface CertificateCreateResponse {
  message: string;
  certificate: Certificate;
}

@Injectable({
  providedIn: 'root'
})
export class CertificateService {
  private readonly http = inject(HttpClient);

  private readonly apiUrl =
    'http://127.0.0.1:8000/api/certificates';

  getCertificates(): Observable<Certificate[]> {
    return this.http.get<Certificate[]>(
      `${this.apiUrl}/my/`
    );
  }

  getCertificate(id: number): Observable<Certificate> {
    return this.http.get<Certificate>(
      `${this.apiUrl}/${id}/`
    );
  }

  createCertificate(
    data: CertificateCreateRequest
  ): Observable<CertificateCreateResponse> {
    return this.http.post<CertificateCreateResponse>(
      `${this.apiUrl}/`,
      data
    );
  }

  verifyCertificate(
    certificateId: string
  ): Observable<Certificate> {
    return this.http.get<Certificate>(
      `${this.apiUrl}/verify/${certificateId}/`
    );
  }
} 