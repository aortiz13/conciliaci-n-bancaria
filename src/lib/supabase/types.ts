/**
 * Tipos de la base de datos Supabase.
 *
 * El esquema `conciliacion` está escrito a mano y refleja
 * `supabase/migrations/*.sql`. Mantener sincronizado al cambiar el schema.
 *
 * El generador automático del MCP solo emite el esquema `public` (la otra app
 * del proyecto), por eso `conciliacion` se mantiene manualmente. Alternativa:
 *   supabase gen types typescript --project-id <ref> --schema conciliacion
 */
export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Database = {
  conciliacion: {
    Tables: {
      plans: {
        Row: {
          id: string;
          nombre: string;
          precio_mes: number;
          docs_incluidos: number;
          extra_doc: number | null;
          tope_duro: boolean;
        };
        Insert: {
          id: string;
          nombre: string;
          precio_mes?: number;
          docs_incluidos: number;
          extra_doc?: number | null;
          tope_duro?: boolean;
        };
        Update: {
          id?: string;
          nombre?: string;
          precio_mes?: number;
          docs_incluidos?: number;
          extra_doc?: number | null;
          tope_duro?: boolean;
        };
        Relationships: [];
      };
      tenants: {
        Row: {
          id: string;
          nombre: string;
          nif: string | null;
          plan_id: string;
          email_alias: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          nombre: string;
          nif?: string | null;
          plan_id?: string;
          email_alias?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          nombre?: string;
          nif?: string | null;
          plan_id?: string;
          email_alias?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
      users: {
        Row: { id: string; email: string; created_at: string };
        Insert: { id: string; email: string; created_at?: string };
        Update: { id?: string; email?: string; created_at?: string };
        Relationships: [];
      };
      memberships: {
        Row: {
          id: string;
          tenant_id: string;
          user_id: string;
          role: Database["conciliacion"]["Enums"]["membership_role"];
          created_at: string;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          user_id: string;
          role?: Database["conciliacion"]["Enums"]["membership_role"];
          created_at?: string;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          user_id?: string;
          role?: Database["conciliacion"]["Enums"]["membership_role"];
          created_at?: string;
        };
        Relationships: [];
      };
      suppliers: {
        Row: {
          id: string;
          tenant_id: string;
          nombre: string | null;
          nif: string | null;
          iban: string | null;
          estado: Database["conciliacion"]["Enums"]["supplier_status"];
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          nombre?: string | null;
          nif?: string | null;
          iban?: string | null;
          estado?: Database["conciliacion"]["Enums"]["supplier_status"];
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          nombre?: string | null;
          nif?: string | null;
          iban?: string | null;
          estado?: Database["conciliacion"]["Enums"]["supplier_status"];
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
      channel_identities: {
        Row: {
          id: string;
          tenant_id: string;
          supplier_id: string;
          tipo: Database["conciliacion"]["Enums"]["channel_type"];
          valor: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          supplier_id: string;
          tipo: Database["conciliacion"]["Enums"]["channel_type"];
          valor: string;
          created_at?: string;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          supplier_id?: string;
          tipo?: Database["conciliacion"]["Enums"]["channel_type"];
          valor?: string;
          created_at?: string;
        };
        Relationships: [];
      };
      documents: {
        Row: {
          id: string;
          tenant_id: string;
          storage_path: string;
          mime: string | null;
          hash: string | null;
          origen_canal: Database["conciliacion"]["Enums"]["channel_type"] | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          storage_path: string;
          mime?: string | null;
          hash?: string | null;
          origen_canal?:
            | Database["conciliacion"]["Enums"]["channel_type"]
            | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          storage_path?: string;
          mime?: string | null;
          hash?: string | null;
          origen_canal?:
            | Database["conciliacion"]["Enums"]["channel_type"]
            | null;
          created_at?: string;
        };
        Relationships: [];
      };
      invoices: {
        Row: {
          id: string;
          tenant_id: string;
          supplier_id: string | null;
          document_id: string | null;
          serie: string | null;
          numero: string | null;
          fecha_expedicion: string | null;
          fecha_operacion: string | null;
          nif_emisor: string | null;
          nif_receptor: string | null;
          base_total: number | null;
          cuota_total: number | null;
          irpf: number;
          total: number | null;
          estado: Database["conciliacion"]["Enums"]["invoice_status"];
          confidence_global: number | null;
          external_ref: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          supplier_id?: string | null;
          document_id?: string | null;
          serie?: string | null;
          numero?: string | null;
          fecha_expedicion?: string | null;
          fecha_operacion?: string | null;
          nif_emisor?: string | null;
          nif_receptor?: string | null;
          base_total?: number | null;
          cuota_total?: number | null;
          irpf?: number;
          total?: number | null;
          estado?: Database["conciliacion"]["Enums"]["invoice_status"];
          confidence_global?: number | null;
          external_ref?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          supplier_id?: string | null;
          document_id?: string | null;
          serie?: string | null;
          numero?: string | null;
          fecha_expedicion?: string | null;
          fecha_operacion?: string | null;
          nif_emisor?: string | null;
          nif_receptor?: string | null;
          base_total?: number | null;
          cuota_total?: number | null;
          irpf?: number;
          total?: number | null;
          estado?: Database["conciliacion"]["Enums"]["invoice_status"];
          confidence_global?: number | null;
          external_ref?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
      invoice_lines: {
        Row: {
          id: string;
          tenant_id: string;
          invoice_id: string;
          descripcion: string | null;
          cantidad: number | null;
          precio_unit: number | null;
          importe: number | null;
          tipo_iva: number | null;
          confidence: number | null;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          invoice_id: string;
          descripcion?: string | null;
          cantidad?: number | null;
          precio_unit?: number | null;
          importe?: number | null;
          tipo_iva?: number | null;
          confidence?: number | null;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          invoice_id?: string;
          descripcion?: string | null;
          cantidad?: number | null;
          precio_unit?: number | null;
          importe?: number | null;
          tipo_iva?: number | null;
          confidence?: number | null;
        };
        Relationships: [];
      };
      invoice_tax_subtotals: {
        Row: {
          id: string;
          tenant_id: string;
          invoice_id: string;
          tipo_iva: number;
          base: number;
          cuota: number;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          invoice_id: string;
          tipo_iva: number;
          base: number;
          cuota: number;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          invoice_id?: string;
          tipo_iva?: number;
          base?: number;
          cuota?: number;
        };
        Relationships: [];
      };
      bank_statements: {
        Row: {
          id: string;
          tenant_id: string;
          formato: Database["conciliacion"]["Enums"]["statement_format"];
          fichero_path: string | null;
          periodo_desde: string | null;
          periodo_hasta: string | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          formato: Database["conciliacion"]["Enums"]["statement_format"];
          fichero_path?: string | null;
          periodo_desde?: string | null;
          periodo_hasta?: string | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          formato?: Database["conciliacion"]["Enums"]["statement_format"];
          fichero_path?: string | null;
          periodo_desde?: string | null;
          periodo_hasta?: string | null;
          created_at?: string;
        };
        Relationships: [];
      };
      bank_movements: {
        Row: {
          id: string;
          tenant_id: string;
          statement_id: string;
          fecha: string;
          importe: number;
          concepto: string | null;
          contrapartida: string | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          statement_id: string;
          fecha: string;
          importe: number;
          concepto?: string | null;
          contrapartida?: string | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          statement_id?: string;
          fecha?: string;
          importe?: number;
          concepto?: string | null;
          contrapartida?: string | null;
          created_at?: string;
        };
        Relationships: [];
      };
      reconciliation_matches: {
        Row: {
          id: string;
          tenant_id: string;
          tipo: string;
          score: number | null;
          estado: Database["conciliacion"]["Enums"]["match_status"];
          importe_asignado: number | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          tipo: string;
          score?: number | null;
          estado?: Database["conciliacion"]["Enums"]["match_status"];
          importe_asignado?: number | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          tipo?: string;
          score?: number | null;
          estado?: Database["conciliacion"]["Enums"]["match_status"];
          importe_asignado?: number | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
      match_links: {
        Row: {
          id: string;
          tenant_id: string;
          match_id: string;
          invoice_id: string;
          movement_id: string;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          match_id: string;
          invoice_id: string;
          movement_id: string;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          match_id?: string;
          invoice_id?: string;
          movement_id?: string;
        };
        Relationships: [];
      };
      exceptions_queue: {
        Row: {
          id: string;
          tenant_id: string;
          tipo: Database["conciliacion"]["Enums"]["exception_type"];
          ref_id: string;
          motivo: string | null;
          estado: Database["conciliacion"]["Enums"]["exception_status"];
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          tipo: Database["conciliacion"]["Enums"]["exception_type"];
          ref_id: string;
          motivo?: string | null;
          estado?: Database["conciliacion"]["Enums"]["exception_status"];
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          tipo?: Database["conciliacion"]["Enums"]["exception_type"];
          ref_id?: string;
          motivo?: string | null;
          estado?: Database["conciliacion"]["Enums"]["exception_status"];
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
      conversations: {
        Row: {
          id: string;
          tenant_id: string;
          supplier_id: string | null;
          canal: Database["conciliacion"]["Enums"]["channel_type"];
          created_at: string;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          supplier_id?: string | null;
          canal: Database["conciliacion"]["Enums"]["channel_type"];
          created_at?: string;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          supplier_id?: string | null;
          canal?: Database["conciliacion"]["Enums"]["channel_type"];
          created_at?: string;
        };
        Relationships: [];
      };
      messages: {
        Row: {
          id: string;
          tenant_id: string;
          conversation_id: string;
          direccion: Database["conciliacion"]["Enums"]["message_direction"];
          contenido: string | null;
          intento: number;
          created_at: string;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          conversation_id: string;
          direccion: Database["conciliacion"]["Enums"]["message_direction"];
          contenido?: string | null;
          intento?: number;
          created_at?: string;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          conversation_id?: string;
          direccion?: Database["conciliacion"]["Enums"]["message_direction"];
          contenido?: string | null;
          intento?: number;
          created_at?: string;
        };
        Relationships: [];
      };
      usage_counters: {
        Row: {
          id: string;
          tenant_id: string;
          periodo: string;
          docs_count: number;
          extras_count: number;
          updated_at: string;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          periodo: string;
          docs_count?: number;
          extras_count?: number;
          updated_at?: string;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          periodo?: string;
          docs_count?: number;
          extras_count?: number;
          updated_at?: string;
        };
        Relationships: [];
      };
      audit_log: {
        Row: {
          id: string;
          tenant_id: string;
          actor: string | null;
          accion: string;
          entidad: string | null;
          antes: Json | null;
          despues: Json | null;
          ts: string;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          actor?: string | null;
          accion: string;
          entidad?: string | null;
          antes?: Json | null;
          despues?: Json | null;
          ts?: string;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          actor?: string | null;
          accion?: string;
          entidad?: string | null;
          antes?: Json | null;
          despues?: Json | null;
          ts?: string;
        };
        Relationships: [];
      };
      erp_connections: {
        Row: {
          id: string;
          tenant_id: string;
          erp_type: Database["conciliacion"]["Enums"]["erp_type"];
          credenciales_cifradas: string | null;
          estado: string;
          ultima_sync: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          tenant_id: string;
          erp_type: Database["conciliacion"]["Enums"]["erp_type"];
          credenciales_cifradas?: string | null;
          estado?: string;
          ultima_sync?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          tenant_id?: string;
          erp_type?: Database["conciliacion"]["Enums"]["erp_type"];
          credenciales_cifradas?: string | null;
          estado?: string;
          ultima_sync?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
    };
    Views: Record<string, never>;
    Functions: {
      is_tenant_member: {
        Args: { p_tenant_id: string };
        Returns: boolean;
      };
      is_tenant_admin: {
        Args: { p_tenant_id: string };
        Returns: boolean;
      };
    };
    Enums: {
      membership_role: "admin" | "operator";
      supplier_status: "provisional" | "activo" | "cuarentena";
      channel_type: "telegram" | "email" | "phone";
      invoice_status:
        | "registrada"
        | "registrada_revision"
        | "escalada"
        | "conciliada"
        | "pagada";
      statement_format: "n43" | "csv" | "xlsx";
      match_status: "propuesto" | "confirmado" | "rechazado" | "manual";
      exception_type: "dato_faltante" | "match_ambiguo" | "ilegible";
      exception_status: "abierta" | "resuelta" | "descartada";
      message_direction: "in" | "out";
      erp_type: "holded" | "a3erp" | "sage200" | "sage50";
    };
    CompositeTypes: Record<string, never>;
  };
};

// Atajos de tipos para filas/inserts/updates del esquema `conciliacion`.
type Schema = Database["conciliacion"];

export type Tables<T extends keyof Schema["Tables"]> =
  Schema["Tables"][T]["Row"];
export type TablesInsert<T extends keyof Schema["Tables"]> =
  Schema["Tables"][T]["Insert"];
export type TablesUpdate<T extends keyof Schema["Tables"]> =
  Schema["Tables"][T]["Update"];
export type Enums<T extends keyof Schema["Enums"]> = Schema["Enums"][T];
