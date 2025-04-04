// src/lib/supabase.ts
import { createClient } from '@supabase/supabase-js';

// IMPORTANTE: Debes reemplazar estos valores con tus credenciales reales de Supabase
// Puedes encontrar estas credenciales en la sección de configuración de tu proyecto en Supabase
// 1. Ve a https://supabase.com y accede a tu cuenta
// 2. Selecciona tu proyecto
// 3. Ve a Configuración del proyecto > API
// 4. Copia la URL y la anon key

const supabaseUrl = import.meta.env.PUBLIC_SUPABASE_URL;
const supabaseKey = import.meta.env.PUBLIC_SUPABASE_KEY;

// Verificación básica para asegurarse de que las credenciales han sido configuradas
if (!supabaseUrl || !supabaseKey) {
  console.warn('⚠️ ADVERTENCIA: Debes configurar tus credenciales reales de Supabase en el archivo .env');
}

export const supabase = createClient(supabaseUrl, supabaseKey);

// Function to get all memories
export async function getRecuerdos() {
  try {
    const { data, error } = await supabase
      .from('recuerdos')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) throw error;
    return data || [];
  } catch (error: any) {
    console.error('Error fetching memories:', {
      name: error.name,
      message: error.message,
      details: error?.details
    });
    return [];
  }
}

// Function to get a specific memory by ID
export async function getRecuerdoById(id: string) {
  try {
    const { data, error } = await supabase
      .from('recuerdos')
      .select('*')
      .eq('id', id)
      .single();

    if (error) throw error;
    return data;
  } catch (error: any) {
    console.error('Error fetching memory:', {
      name: error.name,
      message: error.message,
      details: error?.details
    });
    return null;
  }
}

// Function to create a new memory
export async function createRecuerdo(recuerdo: {
  titulo: string;
  descripcion: string;
  imagen_url?: string;
}) {
  try {
    // Validate input
    if (!recuerdo.titulo || !recuerdo.descripcion) {
      throw new Error('Title and description are required');
    }

    // Add created_at timestamp and user_id if needed
    const recuerdoWithMetadata = {
      ...recuerdo,
      created_at: new Date().toISOString(),
      user_id: 'anonymous' // Add this if your table requires it
    };

    console.log('Attempting to create recuerdo:', recuerdoWithMetadata);

    // First check if the table exists and we can access it
    const { error: checkError } = await supabase
      .from('recuerdos')
      .select('id')
      .limit(1);

    if (checkError) {
      console.error('Error checking recuerdos table:', checkError);
      throw new Error(`Database access error: ${checkError.message}`);
    }

    // Proceed with insert
    const { data, error } = await supabase
      .from('recuerdos')
      .insert([recuerdoWithMetadata])
      .select()
      .single();

    if (error) {
      console.error('Supabase insert error details:', {
        error,
        code: error.code,
        msg: error.message,
        details: error.details
      });
      throw error;
    }

    if (!data) {
      throw new Error('No data returned after insert');
    }

    console.log('Successfully created recuerdo:', data);
    return data;
  } catch (error: any) {
    console.error('Error creating memory:', {
      name: error.name,
      message: error.message,
      code: error?.code,
      details: error?.details,
      hint: error?.hint
    });
    throw error;
  }
}

// Function to upload an image
export async function uploadImage(file: File | Blob, path: string) {
  try {
    if (!file) {
      throw new Error('Invalid file');
    }

    // Generate a unique filename to avoid conflicts
    const timestamp = new Date().getTime();
    const uniquePath = `${timestamp}_${path}`;

    const fileBuffer = await file.arrayBuffer().then(buffer => new Uint8Array(buffer));
    const contentType = file instanceof File ? file.type : 'application/octet-stream';

    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('recuerdos-imagenes')
      .upload(uniquePath, fileBuffer, {
        contentType,
        upsert: false
      });

    if (uploadError) {
      console.error('Upload error details:', uploadError);
      throw uploadError;
    }

    if (!uploadData?.path) {
      throw new Error('No upload data returned');
    }

    const { data: publicUrlData } = supabase.storage
      .from('recuerdos-imagenes')
      .getPublicUrl(uploadData.path);

    if (!publicUrlData?.publicUrl) {
      throw new Error('Failed to get public URL for uploaded image');
    }

    return publicUrlData.publicUrl;
  } catch (error: any) {
    console.error('Error uploading image:', {
      name: error.name,
      message: error.message,
      details: error?.details
    });
    throw error;
  }
}